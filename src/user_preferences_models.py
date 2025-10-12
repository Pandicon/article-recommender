from __future__ import annotations

from dataclasses import dataclass
import sklearn.ensemble
import numpy

import user_preferences

# Chat-GPTed, hopefully works 😅
MODEL_PARAMETRES = {
    0: {
        "n_estimators": 10, "max_depth": 2, "min_samples_leaf": 1
    },
    20: {
        "n_estimators": 30, "max_depth": 4, "min_samples_leaf": 2
    },
    50: {
        "n_estimators": 50, "max_depth": 8, "min_samples_leaf": 3
    },
    100: {
        "n_estimators": 150, "max_depth": None, "min_samples_leaf": 4
    },
    300: {
        "n_estimators": 300, "max_depth": None, "min_samples_leaf": 5
    }
}
RANDOM_STATE = 42

@dataclass
class UserPreferencesModels:
    fluffiness_model: sklearn.ensemble.RandomForestRegressor
    title_descriptiveness_model: sklearn.ensemble.RandomForestRegressor
    def __init__(self, user_preferences: user_preferences.UserPreferences):
        self.fluffiness_model = UserPreferencesModels.get_model(user_preferences.fluffiness)
        self.title_descriptiveness_model = UserPreferencesModels.get_model(user_preferences.title_descriptiveness)
    
    @staticmethod
    def get_model(data: list[user_preferences.PredicatedActual]) -> sklearn.ensemble.RandomForestRegressor:
        x_data = numpy.array([point.machine_rating for point in data]).reshape((-1, 1))
        y_data = numpy.array([point.user_rating for point in data])
        data_size = len(x_data)
        lower_limits = list(MODEL_PARAMETRES.keys())
        lower_limits.sort()
        parametres = MODEL_PARAMETRES[0]
        for i, value in enumerate(lower_limits):
            if value > data_size:
                if i > 0:
                    parametres = MODEL_PARAMETRES[i-1]
                break
        model = sklearn.ensemble.RandomForestRegressor(
            n_estimators=parametres["n_estimators"],       # Fewer trees to prevent overfitting + faster
            max_depth=parametres["max_depth"],           # Limit depth to avoid memorizing
            min_samples_leaf=parametres["min_samples_leaf"],    # Forces each leaf to have at least 2 samples
            random_state=RANDOM_STATE
        )
        model.fit(x_data, y_data)
        return model