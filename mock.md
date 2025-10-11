## Adding preferences
Have the user be able to paste a link to an article they read and add some feedback on it.

Have gemini analyse it and show it to the user where relevant, so that they can react to the analysis. Have an option to regenerate parts of the analysis if it is not really true.
 - Did the themes interest them? (case-by-case), 0-10 scale
 - Was the fluffiness of the language too little, or too much? A 0-10 score of fluffiness is given by gemini and the user will react with -1 to 1 of way too little to way too much.
 - Ad-to-content ratio - how many ads were displayed compared to how much text was on the page, kind of words-per-ads. Add a multiplier of how many ads would be ok compared to this (0-inf)
 - Clickbait score of 0-10 provided by Gemini, was the clickbait level ok for the user? Or was it too clickbaity?

Based on the responses, build a user profile by averaging the responses and saving it to a file:
```json
{
    "interests": {
        "theme1": {
            "score": 2.2, "articles_analysed": 17
        },
        "theme2": {
            "score": 8.3, "articles_analysed": 9
        },
        "theme3": {
            "score": 5.7, "articles_analysed": 3
        }
    },
    "fluffiness": {
        "score": 3.1, "articles_analysed": 29
    },
    "words_per_ad": {
        "score": 394, "articles_analysed": 29
    },
    "max_clickbait": {
        "score": 1.9, "articles_analysed": 29
    }
}
```
When editing the score by adding a new article, just change the average