import user_preferences

PREFERENCES_PATH = ".\\user_preferences.json"

# pylint: disable=missing-function-docstring
def main():
    user_preferences.load(PREFERENCES_PATH)
# pylint: enable=missing-function-docstring

if __name__ == "__main__":
    main()