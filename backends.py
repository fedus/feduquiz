#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from helpers import get_categories

# Backend settings

backends = {
    "opentdb": {
        "name": "Open Trivia DB",
        "url": "https://opentdb.com/api.php",
        "token": "https://opentdb.com/api_token.php?command=request",
        "categories": get_categories()

    },
    "feduquizdb": {
        "name": "Feduquiz DB",
        "url": "https://dillendapp.eu/feduquizdb/api/trivia",
        "token": "https://dillendapp.eu/feduquizdb/api/token/request",
        "categories": [
            ["All", -1],
            ["General knowledge", 1],
            ["Luxemburgensia", 2],
            ["Cooking & baking", 3],
            ["Italianità", 4],
            ["Die bucklige Verwandtschaft",9],
            ["Scotland!!!",15]
        ]
    }
}
