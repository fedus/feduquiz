#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def get_verdict(score):
    if score == 1:              # 100 %
        return "Perfect!"
    elif 0.9 <= score < 1:      # 90-99 %
        return "Great!"
    elif 0.6 <= score < 0.9:    # 60-89 %
        return "Not bad!"
    elif 0.5 < score < 60:      # 51-59 %
        return "Room for improvement!"
    elif score == 0.5:          # 50 %
        return "Juuuust made it!"
    elif 0.4 <= score < 0.5:    # 40-49 %
        return "That didn't quite work out!"
    elif 0.1 <= score < 0.4:    # 10-39 %
        return "You better improve!"
    elif 0 < score < 0.1:       # 1-9 %
        return "Just ... bad!"
    else:                       # 0 %
        return "Holy crap that was bad!"

def get_categories():
    raw = '{"trivia_categories":[{"id":9,"name":"General Knowledge"},{"id":10,"name":"Books"},{"id":11,"name":"Film"},{"id":12,"name":"Music"},{"id":13,"name":"Musicals & Theatres"},{"id":14,"name":"Television"},{"id":15,"name":"Video Games"},{"id":16,"name":"Board Games"},{"id":17,"name":"Science & Nature"},{"id":18,"name":"Computers"},{"id":19,"name":"Mathematics"},{"id":20,"name":"Mythology"},{"id":21,"name":"Sports"},{"id":22,"name":"Geography"},{"id":23,"name":"History"},{"id":24,"name":"Politics"},{"id":25,"name":"Art"},{"id":26,"name":"Celebrities"},{"id":27,"name":"Animals"},{"id":28,"name":"Vehicles"},{"id":29,"name":"Comics"},{"id":30,"name":"Gadgets"},{"id":31,"name":"Jap. Anime & Manga"},{"id":32,"name":"Cartoon & Animations"}]}'
    parsed = json.loads(raw)['trivia_categories']
    result = [['All', 0]]
    for cat_pair in parsed:
        result.append([cat_pair['name'], cat_pair['id']])
    print(result)
    return result