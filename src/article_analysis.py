from dataclasses import dataclass
import fetch_article
import json
import google.generativeai
import typing
import user_preferences
import user_preferences_models
import main

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

        if self.main_themes == None:
            self.main_themes = []

def analyse_article(model: google.generativeai.GenerativeModel, url: str, user_preferences: user_preferences.UserPreferences) -> ArticleAnalysis:
    """
    Uses an LLM to generate raw scores about the article
    """
    metadata = fetch_article.extract_article_metadata(fetch_article.fetch_article(url))
    prompt = metadata.format_for_llm() + "\n" + user_preferences.format_for_llm()
    response = model.generate_content(prompt)
    response_text = response.text.strip().removeprefix("```json").removeprefix("```").removeprefix("`").removesuffix("```").removesuffix("`").strip()
    return ArticleAnalysis(response_text)

def rate_article(article_analysis: ArticleAnalysis, user_preferences_models: user_preferences_models.UserPreferencesModels):
    """
    Generates the scores for the article from the raw data from the LLM
    """
    themes_alignment_score = article_analysis.main_themes_alignment
    fluffiness_alignment_score = None if article_analysis.how_fluffy == None else user_preferences_models.fluffiness_model.predict([[article_analysis.how_fluffy]])[0]
    title_descriptiveness_score = None if article_analysis.how_descriptive_title == None else user_preferences_models.title_descriptiveness_model.predict([[article_analysis.how_descriptive_title]])[0]
    combined_score = combine_scores([themes_alignment_score, fluffiness_alignment_score, title_descriptiveness_score])

    print(themes_alignment_score, fluffiness_alignment_score, title_descriptiveness_score, combined_score)

def combine_scores(scores: list[float]) -> float:
    """
    Combines a list of scores into a single score
    """
    S = 0.1
    def transform(x: float) -> float:
        return x*(main.MAX_SCORE - S)/main.MAX_SCORE + S
    
    def inverse_transform(x: float) -> float:
        return main.MAX_SCORE/(main.MAX_SCORE - S)*(x-S)

    p = 0.25
    return inverse_transform(pow(sum([pow(transform(score), p) for score in scores]) / len(scores), 1/p))