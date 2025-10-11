from __future__ import annotations

from dataclasses import dataclass
import json
import typing

RawJsonDict: typing.TypeAlias = dict[str, typing.Union["ScoreInformation", dict[str, "ScoreInformation"]]]

@dataclass
class UserPreferences:
    interests: dict[str, dict[str, ScoreInformation]]
    fluffiness: ScoreInformation
    words_per_ad: ScoreInformation
    max_clickbait: ScoreInformation
    def __init__(self, json_dict: RawJsonDict):
        default_preferences = UserPreferences.default_raw()
        for key, default_value in default_preferences.items():
            setattr(self, key, json_dict[key] if key in json_dict.keys() else default_value)

    @staticmethod
    def default() -> UserPreferences:
        return UserPreferences(UserPreferences.default_raw())

    @staticmethod
    def default_raw() -> RawJsonDict:
        return {
            "interests": {},
            "fluffiness": ScoreInformation(0.0, 0),
            "words_per_ad": ScoreInformation(0.0, 0),
            "max_clickbait": ScoreInformation(0.0, 0)
        }

@dataclass
class ScoreInformation:
    score: float
    articles_analysed: int
    def __init__(self, score: float, articles_analysed: int):
        self.score = score
        self.articles_analysed = articles_analysed

def load(preferences_path: str) -> UserPreferences:
    """
    Loads the user preferences JSON file, handling the case of a missing/empty file
    """
    try:
        with open(preferences_path, 'r') as file:
            content = file.read().strip()
            is_empty = len(content) == 0
            if not is_empty:
                data = json.loads(content)
                user_preferences = UserPreferences(data)
                return user_preferences
            print(f"Warning: '{preferences_path}' is empty. Returning an empty dictionary.")
            return UserPreferences.default()
    except FileNotFoundError:
        print(f"Error: The file '{preferences_path}' was not found.")
        return UserPreferences.default()
    except json.JSONDecodeError as e:
        print(f"Error: Failed to decode JSON from '{preferences_path}'. {e}")
        return UserPreferences.default()