import google.generativeai
import os
import sys
import logging
import time
import dotenv
import json
import user_preferences_models
import article_analysis
import user_preferences_handler
import constants

SYSTEM_INSTRUCTION = """You are a model tasked with analyzing articles and rating certain qualities objectively. You will receive:
- The article title
- The article text
- A dictionary of user interests as theme-score pairs (scores range from 0 = not interested to 10 = main interest)
Your job is to:
1. Rate fluffiness of the article text:
- Rate how "fluffy" the article text is on a scale from 0 to 10:
- 0 = very raw, factual, concise, informative, only facts are presented (like a scientific paper or straightforward report)
- 5 = Some filler or vague language, but contains substantial information
- 10 = extremely fluffy, verbose, filled with filler or vague language, where the reader gains little meaningful information despite article length
- Consider the density of meaningful, concrete information versus vague, filler, or redundant content.

2. Rate how descriptive the title is:
- Rate how well the title describes the article content on a scale from 0 to 10:
- 0 = very clickbait, misleading, or unrelated to the article
- 10 = fully descriptive, accurately reflects the article content

3. Rate theme alignment with user interests:
- Carefully read the entire article and infer the overall themes and subjects, even if these themes are not explicitly mentioned as keywords.
- Consider which themes from the user's interests dictionary best describe the article's main topics, either directly or by close semantic relation.
- Use your best judgment to estimate how strongly each theme from the user's interests is present or relevant in the article.
- Assign an alignment score from 0 to 10, reflecting how likely it is that the user would find the article interesting based on their interests.
- A score of 0 means the article's content is almost completely unrelated or uninteresting to the user's interests.
- A score of 10 means the article perfectly matches the user's main interests.
- The alignment score must be independent of fluffiness or title descriptiveness scores.
- If the article focuses mainly on themes the user rates low, the alignment score should be low. If it matches themes rated high, the score should be high.
- If the article's content is ambiguous or neutral regarding user interests, assign a score near the middle (around 5).
- For example, if the user interest dictionary is {'fun': 8, 'sports': 9, politics: '2'} and the article is about upcoming elections, a reasonable score would be around 2. If, however, the article was about a new sports centre opening, a good score would be around 8-9.

4. Extract main themes:
- Extract 3 to 7 main themes from the article. Each theme should be very short (1-2 words), general, and in English (translate if necessary). These themes should act like tags that summarize the article's core topics.

You must respond only with JSON in plain text, without any markdown or formatting such as ```json and similar. The JSON format is the following:
{"main_themes": ['theme1', 'theme2, ...], "main_themes_alignment": float, "how_fluffy": float, "how_descriptive_title": float}
"""

logging.Formatter.converter = time.gmtime
logging.basicConfig(
    format="%(asctime)s.%(msecs)03dZ %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO
)

# pylint: disable=missing-function-docstring
def main():
    logging.debug(SYSTEM_INSTRUCTION)
    dotenv.load_dotenv()
    preferences = user_preferences_handler.load(constants.PREFERENCES_PATH)
    preferences_prediction_models = user_preferences_models.UserPreferencesModels(preferences)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY is None:
        logging.error("The Google API key must be set to the GOOGLE_API_KEY environment variable")
        sys.exit(1)

    google.generativeai.configure(api_key=GOOGLE_API_KEY)
    available_model_names_list = [model.name for model in google.generativeai.list_models()]
    available_model_names_list.sort()
    available_model_names = ", ".join(available_model_names_list)
    model_name = ""
    while not model_name in available_model_names_list:
        model_name = input(f"Please choose a model name from the following list: {available_model_names}\n")
    model = google.generativeai.GenerativeModel(model_name, system_instruction=SYSTEM_INSTRUCTION)

    VALID_ACTIONS_FULL = ["analyse article", "rate article", "change model", "exit"]
    ALIASES = {"analyse article": ["a"], "rate article": ["r"], "change model": ["c"], "exit": ["e"]}
    all_valid_actions = VALID_ACTIONS_FULL.copy()
    actions_with_aliases = []
    for valid_action in VALID_ACTIONS_FULL:
        if not valid_action in ALIASES.keys():
            actions_with_aliases.append(valid_action)
            continue
        all_valid_actions.extend(ALIASES[valid_action])
        actions_with_aliases.append(f"{valid_action} ({", ".join(ALIASES[valid_action])})")
    actions_with_aliases_str = ", ".join(actions_with_aliases)

    while True:
        action = ""
        while not action in all_valid_actions:
            action = input(f"Please choose the action you want to take from the following list: {actions_with_aliases_str}\n")
            action = action.strip().lower()
            if not action in VALID_ACTIONS_FULL:
                for a in VALID_ACTIONS_FULL:
                    if not a in ALIASES.keys():
                        continue
                    if action in ALIASES[a]:
                        action = a
                        break
        if action == "exit":
            break

        if action == "analyse article":
            url = input("URL to analyse: ")
            article_analysis_result = article_analysis.analyse_article(model, url, preferences)
            if article_analysis_result is None:
                print("Error: The article analysis failed unexpectedly. Please try again later.")
                continue
            article_scores = article_analysis.rate_article(article_analysis_result, preferences_prediction_models)
            print(f"Article title: {article_analysis_result.title}\n" +
                  f"Article source: {article_analysis_result.hostname}\n" +
                  f"Main themes: {", ".join(article_analysis_result.main_themes)}\n" + 
                  f"Main themes alignment: {article_scores.main_themes_alignment:.1f}/10\n" +
                  f"Fluffiness: {article_scores.fluffiness_alignment:.1f}/10 (absolute score: {article_analysis_result.how_fluffy:.1f})\n" +
                  f"Title descriptiveness: {article_scores.title_descriptiveness:.1f}/10 (absolute score: {article_analysis_result.how_descriptive_title:.1f})\n" +
                  f"Overall score: {article_scores.overall:.1f}/10")
            
        if action == "change model":
            model_name = ""
            while not model_name in available_model_names_list:
                model_name = input(f"Please choose a model name from the following list: {available_model_names}\n")
            model = google.generativeai.GenerativeModel(model_name, system_instruction=SYSTEM_INSTRUCTION)

        STOP_SEQUENCE = ":done"
        if action == "rate article":
            url = input("URL of the article: ")
            print("Main themes of the article")
            theme_ratings = []
            theme = ""
            while True:
                theme = input(f"Enter the next theme (or '{STOP_SEQUENCE}' to finish rating themes): ")
                if theme.lower() == STOP_SEQUENCE:
                    break
                rating = 0
                got_a_good_float = False
                while not got_a_good_float:
                    rating_str = input(f"Enter your interest in the '{theme}' theme as a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f} (or '{STOP_SEQUENCE}' to finish rating themes): ")
                    if rating_str.lower() == STOP_SEQUENCE:
                        break
                    rating = 0.0
                    try:
                        rating = float(rating_str)
                        if rating > constants.MAX_SCORE or rating < constants.MIN_SCORE:
                            print(f"Error: The rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
                            continue
                        got_a_good_float = True
                    except ValueError:
                        print(f"Error: The rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
                theme_ratings.append({"theme": theme, "rating": rating})
            
            fluffiness = 0.0
            got_fluffiness = False
            while not got_fluffiness:
                fluffiness_str = input(f"Enter how you liked the 'fluffiness' (i.e. if the amount of filler language suited you well or if it was not the right amount) of the article as a decimal number between {constants.MIN_SCORE:.1f} (should be very different, does not matter if it should be drier or fluffier) and {constants.MAX_SCORE:.1f} (perfect amount of filler): ")
                try:
                    fluffiness = float(fluffiness_str)
                    if fluffiness > constants.MAX_SCORE or fluffiness < constants.MIN_SCORE:
                        print(f"Error: The fluffiness rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
                        continue
                    got_fluffiness = True
                except ValueError:
                    print(f"Error: The fluffiness rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
            
            title_descriptiveness = 0.0
            got_title_descriptiveness = False
            while not got_title_descriptiveness:
                title_descriptiveness_str = input(f"Enter how decriptive you found the title of the article to be (with respect to the actual content of the article) as a decimal number between {constants.MIN_SCORE:.1f} (should be very different, does not matter if it should be drier or fluffier) and {constants.MAX_SCORE:.1f} (perfect amount of filler): ")
                try:
                    title_descriptiveness = float(title_descriptiveness_str)
                    if title_descriptiveness > constants.MAX_SCORE or title_descriptiveness < constants.MIN_SCORE:
                        print(f"Error: The title descriptiveness rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
                        continue
                    got_title_descriptiveness = True
                except ValueError:
                    print(f"Error: The title descriptiveness rating has to be a decimal number between {constants.MIN_SCORE:.1f} and {constants.MAX_SCORE:.1f}")
            
            VALID_SUBMISSION_ACTIONS_FULL = ["submit", "cancel"]
            SUBMISSION_ALIASES = {"submit": ["s"], "cancel": ["c"]}
            all_valid_submission_actions = VALID_SUBMISSION_ACTIONS_FULL.copy()
            submission_actions_with_aliases = []
            for valid_action in VALID_SUBMISSION_ACTIONS_FULL:
                if not valid_action in SUBMISSION_ALIASES.keys():
                    submission_actions_with_aliases.append(valid_action)
                    continue
                all_valid_submission_actions.extend(SUBMISSION_ALIASES[valid_action])
                submission_actions_with_aliases.append(f"{valid_action} ({", ".join(SUBMISSION_ALIASES[valid_action])})")
            submission_actions_with_aliases_str = ", ".join(submission_actions_with_aliases)
            print(f"You provided the following data about the article:\n" +
                  f"URL: {url}\n" +
                  f"Themes and their ratings: {", ".join(f"{theme_info["theme"]}: {theme_info["rating"]:.1f}" for theme_info in theme_ratings)}\n" +
                  f"Fluffiness: {fluffiness:.1f}\n" +
                  f"Title descriptiveness: {title_descriptiveness:.1f}")
            submission_action = ""
            while not submission_action in all_valid_submission_actions:
                submission_action = input(f"Based on the above summary, choose an action from the following list: {submission_actions_with_aliases_str}\n")
                submission_action = submission_action.strip().lower()
                if not submission_action in VALID_SUBMISSION_ACTIONS_FULL:
                    for a in VALID_SUBMISSION_ACTIONS_FULL:
                        if not a in SUBMISSION_ALIASES.keys():
                            continue
                        if submission_action in SUBMISSION_ALIASES[a]:
                            submission_action = a
                            break
            if submission_action == "cancel":
                continue
            if submission_action == "submit":
                article_analysis_result = article_analysis.analyse_article(model, url, preferences)
                if article_analysis_result is None:
                    print("Error: The article analysis failed unexpectedly. Please try again later.")
                    continue
                for theme_info in theme_ratings:
                    theme = theme_info["theme"]
                    theme_rating = theme_info["rating"]
                    if theme in preferences.interests.keys():
                        preferences.interests[theme].score = (preferences.interests[theme].score * preferences.interests[theme].articles_analysed + theme_rating) / (preferences.interests[theme].articles_analysed + 1)
                        preferences.interests[theme].articles_analysed += 1
                    else:
                        preferences.interests[theme] = user_preferences_handler.ScoreInformation(theme_rating, 1)
                preferences.fluffiness.append(user_preferences_handler.PredicatedActual(article_analysis_result.how_fluffy, fluffiness))
                preferences.title_descriptiveness.append(user_preferences_handler.PredicatedActual(article_analysis_result.how_descriptive_title, title_descriptiveness))
                user_preferences_handler.save(constants.PREFERENCES_PATH, preferences)
                
# pylint: enable=missing-function-docstring

if __name__ == "__main__":
    main()