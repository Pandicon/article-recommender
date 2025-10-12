from __future__ import annotations

from dataclasses import dataclass
import json
import trafilatura
import typing

@dataclass
class ArticleMetadata:
    title: str
    text: str
    hostname: str
    def __init__(self, title: str, text: str, hostname: typing.Optional[str]):
        self.title = title
        self.text = text
        self.hostname = hostname if hostname is not None else "unknown"

    def format_for_llm(self) -> str:
        return f"Title: {self.title}\nSource: {self.hostname}\nText: {self.text}"

def fetch_article(url: str) -> typing.Optional[str]:
    downloaded_page = trafilatura.fetch_url(url)
    return downloaded_page

def extract_article_metadata(webpage: str) -> typing.Optional[ArticleMetadata]:
    extracted_raw = trafilatura.extract(webpage, output_format="json", with_metadata=True)
    if extracted_raw is None:
        return None
    extracted_data = json.loads(extracted_raw)
    return ArticleMetadata(extracted_data.get("title"), extracted_data.get("text"), extracted_data.get("hostname"))