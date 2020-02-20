#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.network.urlrequest import UrlRequest
from html import unescape

import json


class Trivia:
    """Trivia class"""

    def __init__(self, use_sample_data=False):
        self.quiz_data = None
        self.req = None
        self.score = 0
        self.round = 0
        self.running = False
        self.cancel_reason = None
        self.use_sample_data = use_sample_data

    def new_game(self, api_url, difficulty, category, amount, q_type, wait=False):
        self.score = 0
        self.round = 0
        self.fetch_new(api_url, difficulty, category, amount, q_type, wait=wait)

    def get_current_round(self):
        return self.round + 1

    def get_total_rounds(self):
        return len(self.quiz_data) if self.quiz_data else 0

    def get_current_question(self):
        return self.quiz_data[self.round] if (self.running and self.round < len(self.quiz_data)) else False

    def register_answer(self, result):
        if self.running:
            if result:
                self.score += 1
                print("CURRENT SCORE: {}".format(self.score))
            self.round += 1
            if self.round >= len(self.quiz_data):
                self.running = False

    def check_game(self):
        return self.running

    def cancel_game(self, reason=None):
        self.running = False
        self.cancel_reason = reason

    def fetch_new(self, api_url, difficulty, category, amount, q_type, wait=False):
        if self.use_sample_data:
            import json
            with open('./resources/sample_quiz_data.json') as f:
                data = json.load(f)
            self.fetch_success(None, data)
        else:
            base_url = api_url + '?'
            if difficulty is not '':
                base_url += 'difficulty=' + str(difficulty) + '&'
            if category is not 0:
                base_url += 'category=' + str(category) + '&'
            if q_type is not '':
                base_url += 'type=' + str(q_type) + '&'
            base_url += 'amount=' + str(amount)
            self.req = UrlRequest(base_url, on_success=self.fetch_success, on_failure=self.fetch_fail, on_error=self.fetch_error)
            if wait:
                self.req.wait()

    def fetch_success(self, request, result):
        self.quiz_data = self.html_decode(result['results'])
        self.running = True
        try:
            print(self.quiz_data)
            print()
        except:
            # Probably a unicode error.
            print("Could not print quiz data.")

    def fetch_fail(self, request, result):
        print("Failure fetching quiz data: {}".format(result))

    def fetch_error(self, request, error):
        print("Error fetching quiz data: {}".format(error))

    def html_decode(self, quiz_obj):
        """
        URL decodes or unencodes the quiz data recursively.
        Credits to https://nvie.com/posts/modifying-deeply-nested-structures/
        """
        if isinstance(quiz_obj, dict):
            return {k: self.html_decode(v) for k, v in quiz_obj.items()}
        elif isinstance(quiz_obj, list):
            return [self.html_decode(elem) for elem in quiz_obj]
        else:
            return unescape(quiz_obj)

