import dotenv
import google.generativeai
import user_preferences
import user_preferences_models
import article_analysis
import os
import sys
import logging
import time

PREFERENCES_PATH = ".\\user_preferences.json"
SYSTEM_INSTRUCTION_OLD = """You are a model for judging certain qualities of articles. You must judge those objectively. You will always receive information about the article which includes the article title and article text.
Your job is to extract 3-7 main themes of the article (very short and quite general themes, generally 1-2 words, similar to a tag, it MUST be in english (translate if necessary)) and how desriptive the title is (rate it with a float from 0=very much clickbait, the title is very misleading about the article to 10=the article is very much about what the title said).
You will also judge how "fluffy" the article text is. "Fluffy" means the article contains a lot of filler, vague language, repetitions, or content that adds little to no real information. Rate it on a scale from 0 to 10, where 0 means the article is very raw, dense, factual, and informative—like a scientific paper or a very concise report and 10 means the article is extremely fluffy, filled with fluff or filler content, overly verbose, and the reader gains almost no meaningful information despite the length. Consider fluffiness regardless of article length.
You will also receive a dictionary of theme-score pairs representing the user's interests, where scores range from 0 (not interested at all) to 10 (main interest). Your task is to read the article and rate how well its main themes align with the user's interests. Important: Your alignment score must reflect the user's interests, not the objective importance or newsworthiness of the article. If the article's themes match topics with low user interest scores, the alignment should be low—even if the article is about controversial or significant topics. Conversely, if the article's themes strongly match the user's top interests, the score should be high. Rate the alignment as a float from 0 (user not likely to find it interesting at all) to 10 (exactly the user's main interests).
You must respond only with JSON in plain text, without any formatting such as ```json and similar. The JSON format is the following:
{'main_themes': ['theme1', 'theme2, ...], 'main_themes_alignment': float, 'how_fluffy': float, 'how_descriptive_title': float}"""

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

MIN_SCORE = 0
MAX_SCORE = 10

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
    preferences = user_preferences.load(PREFERENCES_PATH)
    preferences_prediction_models = user_preferences_models.UserPreferencesModels(preferences)
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY == None:
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

    url = input("URL to analyse: ")
    article_analysis_result = article_analysis.analyse_article(model, url, preferences)
    logging.info(article_analysis_result)
    article_scores = article_analysis.rate_article(article_analysis_result, preferences_prediction_models)
    logging.info(article_scores)
# pylint: enable=missing-function-docstring

if __name__ == "__main__":
    main()