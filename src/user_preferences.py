from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import typing

RawJsonDict: typing.TypeAlias = dict[str, typing.Union["ScoreInformation", dict[str, "ScoreInformation"]]]

@dataclass
class UserPreferences:
    interests: dict[str, ScoreInformation]
    fluffiness: list[PredicatedActual]
    title_descriptiveness: list[PredicatedActual]
    def __init__(self, json_dict: RawJsonDict):
        default_preferences = UserPreferences.default_raw()
        interests = json_dict["interests"] if "interests" in json_dict.keys() else default_preferences["interests"]
        fluffiness = json_dict["fluffiness"] if "fluffiness" in json_dict.keys() else default_preferences["flufiness"]
        title_descriptiveness = json_dict["title_descriptiveness"] if "title_descriptiveness" in json_dict.keys() else default_preferences["title_descriptiveness"]
        interests = {theme: ScoreInformation(information["score"], information["articles_analysed"]) for theme, information in interests.items()}
        fluffiness = [PredicatedActual(point["machine_rating"], point["user_rating"]) for point in fluffiness]
        title_descriptiveness = [PredicatedActual(point["machine_rating"], point["user_rating"]) for point in title_descriptiveness]
        self.interests = interests
        self.fluffiness = fluffiness
        self.title_descriptiveness = title_descriptiveness

    def format_for_llm(self) -> str:
        res = {interest: score_information.score for interest, score_information in self.interests.items()}
        return str(res)

    @staticmethod
    def default() -> UserPreferences:
        return UserPreferences(UserPreferences.default_raw())

    @staticmethod
    def default_raw() -> RawJsonDict:
        return {
            "interests": {},
            "fluffiness": [],
            "title_descriptiveness": []
        }

@dataclass
class ScoreInformation:
    score: float
    articles_analysed: int
    def __init__(self, score: float, articles_analysed: int):
        self.score = score
        self.articles_analysed = articles_analysed

@dataclass
class PredicatedActual:
    machine_rating: float
    user_rating: float
    def __init__(self, machine_rating: float, user_rating: float):
        self.machine_rating = machine_rating
        self.user_rating = user_rating

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
            logging.warning(f"Warning: '{preferences_path}' is empty. Returning an empty dictionary.")
            return UserPreferences.default()
    except FileNotFoundError:
        logging.error(f"Error: The file '{preferences_path}' was not found.")
        return UserPreferences.default()
    except json.JSONDecodeError as e:
        logging.error(f"Error: Failed to decode JSON from '{preferences_path}'. {e}")
        return UserPreferences.default()