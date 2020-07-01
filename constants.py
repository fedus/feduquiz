#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from helpers import get_categories

# Backend settings

BACKENDS = {
    "opentdb": {
        "url": "https://opentdb.com/api.php",
        "token": "https://opentdb.com/api_token.php?command=request",
        "categories": get_categories()

    },
    "feduquizdb": {
        "url": "https://dillendapp.eu/feduquizdb/api/trivia",
        "token": "http://localhost:5000/api/token/request",
        "categories": [["All", -1], ["General knowledge", 1],["Luxemburgensia", 2],["Cooking & baking", 3],["Italianità", 4]]
    }
}

# Useful constants and strings

CEC_CMD_MAP = {
    "UP": [">> 01:44:01", 273],
    "DOWN": [">> 01:44:02", 274],
    "LEFT": [">> 01:44:03", 276],
    "RIGHT": [">> 01:44:04", 275],
    "OK": [">> 01:44:00", 13, 1073741824],
    "RED": [">> 01:44:72", 114],
    "GREEN": [">> 01:44:73", 103],
    "YELLOW": [">> 01:44:74", 121],
    "BLUE": [">> 01:44:71", 98],
    "EXIT": [">> 01:44:0d", 27],
}

POSITIVES = [
    "Nice!",
    "Great!",
    "Yes!",
    "Right!",
    "Correct!",
    "Yup!",
    "Good!",
]

NEGATIVES = [
    "Oops!",
    "Wrong!",
    "No!",
    "Nope!",
    "Uh oh!",
    "Snap!",
    "Bad!",
]

INSTRUCTION_TEXT = """Use the buttons on your television's remote control to control the game. In the menus, the relevant buttons will be indicated at the bottom of the screen. During the game, answers are given using the coloured buttons.
Use the options menu to adapt the categories, difficulty, number of questions, etc. to your liking. You can also enable or disable functions like instant feedback or the timer.
For multiplayer mode, players have to scan the QR code on the screen and be in the same WiFi or LAN than the machine running the quiz. Players can then respond to questions on their mobile phone."""

SECS_PER_QUESTION = 10
TIMER_WARNING = 0.35

MULTIPLAYER_GAME_PATTERN = 'fq-{}'
MULTIPLAYER_JOIN_LINK_BASE = 'https://dillendapp.eu/feduquiz-client-basic/?gameid={}'