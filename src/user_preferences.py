from __future__ import annotations

from dataclasses import dataclass
import json
import typing

RawJsonDict: typing.TypeAlias = dict[str, typing.Union["ScoreInformation", dict[str, "ScoreInformation"]]]

@dataclass
class UserPreferences:
    interests: dict[str, ScoreInformation]
    fluffiness: ScoreInformation
    words_per_ad: ScoreInformation
    minimum_descriptiveness: ScoreInformation
    def __init__(self, json_dict: RawJsonDict):
        default_preferences = UserPreferences.default_raw()
        interests = json_dict["interests"] if "interests" in json_dict.keys() else default_preferences["interests"]
        fluffiness = json_dict["fluffiness"] if "fluffiness" in json_dict.keys() else default_preferences["flufiness"]
        words_per_ad = json_dict["words_per_ad"] if "words_per_ad" in json_dict.keys() else default_preferences["words_per_ad"]
        minimum_descriptiveness = json_dict["minimum_descriptiveness"] if "minimum_descriptiveness" in json_dict.keys() else default_preferences["minimum_descriptiveness"]
        interests = {theme: ScoreInformation(information["score"], information["articles_analysed"]) for theme, information in interests.items()}
        fluffiness = ScoreInformation(fluffiness["score"], fluffiness["articles_analysed"])
        words_per_ad = ScoreInformation(words_per_ad["score"], words_per_ad["articles_analysed"])
        minimum_descriptiveness = ScoreInformation(minimum_descriptiveness["score"], minimum_descriptiveness["articles_analysed"])
        self.interests = interests
        self.fluffiness = fluffiness
        self.words_per_ad = words_per_ad
        self.minimum_descriptiveness = minimum_descriptiveness

    def format_for_llm(self) -> str:
        for interest, score_information in self.interests.items():
            print(interest, type(score_information))
        res = {interest: score_information.score for interest, score_information in self.interests.items()}
        return str(res)

    @staticmethod
    def default() -> UserPreferences:
        return UserPreferences(UserPreferences.default_raw())

    @staticmethod
    def default_raw() -> RawJsonDict:
        return {
            "interests": {},
            "fluffiness": ScoreInformation(0.0, 0),
            "words_per_ad": ScoreInformation(0.0, 0),
            "minimum_descriptiveness": ScoreInformation(0.0, 0)
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