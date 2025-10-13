"""
Handling of the article fetching and extracting of the metadata
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import typing
import trafilatura

@dataclass
class ArticleMetadata:
    """
    A data structure class for storing the article metadata
    """
    title: str
    text: str
    hostname: str
    def __init__(self, title: str, text: str, hostname: typing.Optional[str]):
        self.title = title
        self.text = text
        self.hostname = hostname if hostname is not None else "unknown"

    def format_for_llm(self) -> str:
        """
        Formats the article metadata for use in a LLM prompt
        """
        return f"Title: {self.title}\nSource: {self.hostname}\nText: {self.text}"

def fetch_article(url: str) -> typing.Optional[str]:
    """
    Fetches the article text from the url provided
    """
    downloaded_page = trafilatura.fetch_url(url)
    return downloaded_page

def extract_article_metadata(webpage: str) -> typing.Optional[ArticleMetadata]:
    """
    Extracts the metadata from the article text
    """
    extracted_raw = trafilatura.extract(webpage, output_format="json", with_metadata=True)
    if extracted_raw is None:
        return None
    extracted_data = json.loads(extracted_raw)
    return ArticleMetadata(extracted_data.get("title"), extracted_data.get("text"), extracted_data.get("hostname"))