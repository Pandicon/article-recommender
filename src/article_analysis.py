from dataclasses import dataclass
import json
import google.generativeai
import typing
import user_preferences_handler
import user_preferences_models
import fetch_article
import constants

@dataclass
class ArticleAnalysis:
    main_themes: list[str]
    main_themes_alignment: typing.Optional[float]
    how_fluffy: typing.Optional[float]
    how_descriptive_title: typing.Optional[float]
    def __init__(self, raw_analysis: str):
        analysis = json.loads(raw_analysis)
        self.main_themes = analysis.get("main_themes")
        self.main_themes_alignment = analysis.get("main_themes_alignment")
        self.how_fluffy = analysis.get("how_fluffy")
        self.how_descriptive_title = analysis.get("how_descriptive_title")

        if self.main_themes is None:
            self.main_themes = []

@dataclass
class ArticleScores:
    main_themes_alignment: float
    fluffiness_alignment: float
    title_descriptiveness: float
    overall: float
    def __init__(self, main_themes_alignment: float, fluffiness_alignment: float, title_descriptiveness: float, overall: float):
        self.main_themes_alignment = main_themes_alignment
        self.fluffiness_alignment = fluffiness_alignment
        self.title_descriptiveness = title_descriptiveness
        self.overall = overall

def analyse_article(model: google.generativeai.GenerativeModel, url: str, user_preferences: user_preferences_handler.UserPreferences) -> ArticleAnalysis:
    """
    Uses an LLM to generate raw scores about the article
    """
    metadata = fetch_article.extract_article_metadata(fetch_article.fetch_article(url))
    prompt = metadata.format_for_llm() + "\n" + user_preferences.format_for_llm()
    response = model.generate_content(prompt)
    response_text = response.text.strip().removeprefix("```json").removeprefix("```").removeprefix("`").removesuffix("```").removesuffix("`").strip()
    return ArticleAnalysis(response_text)

def rate_article(article_analysis: ArticleAnalysis, user_preference_models: user_preferences_models.UserPreferencesModels) -> ArticleScores:
    """
    Generates the scores for the article from the raw data from the LLM
    """
    themes_alignment_score = article_analysis.main_themes_alignment
    fluffiness_alignment_score = None if article_analysis.how_fluffy is None else user_preference_models.fluffiness_model.predict([[article_analysis.how_fluffy]])[0]
    title_descriptiveness_score = None if article_analysis.how_descriptive_title is None else user_preference_models.title_descriptiveness_model.predict([[article_analysis.how_descriptive_title]])[0]
    combined_score = combine_scores(list(filter(lambda x: x is not None, [themes_alignment_score, fluffiness_alignment_score, title_descriptiveness_score])))

    return ArticleScores(themes_alignment_score, fluffiness_alignment_score, title_descriptiveness_score, combined_score)

def combine_scores(scores: list[float]) -> float:
    """
    Combines a list of scores into a single score
    """
    S = 0.1
    def transform(x: float) -> float:
        return x*(constants.MAX_SCORE - S)/constants.MAX_SCORE + S

    def inverse_transform(x: float) -> float:
        return constants.MAX_SCORE/(constants.MAX_SCORE - S)*(x-S)

    p = 0.25
    return inverse_transform(pow(sum([pow(transform(score), p) for score in scores]) / len(scores), 1/p))