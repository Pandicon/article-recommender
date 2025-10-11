from dataclasses import dataclass
import fetch_article
import json
import google.generativeai
import typing
import user_preferences

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
    metadata = fetch_article.extract_article_metadata(fetch_article.fetch_article(url))
    prompt = metadata.format_for_llm() + "\n" + user_preferences.format_for_llm()
    print(prompt)
    response = model.generate_content(prompt)
    response_text = response.text.strip().removeprefix("```json").removeprefix("```").removeprefix("`").removesuffix("```").removesuffix("`").strip()
    print(response_text)
    return ArticleAnalysis(response_text)