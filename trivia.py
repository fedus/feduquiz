#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.properties import DictProperty, BooleanProperty, BoundedNumericProperty, NumericProperty, ObjectProperty, StringProperty, ListProperty
from kivy.network.urlrequest import UrlRequest
from kivy.event import EventDispatcher
from kivy.app import App
from kivy.clock import Clock

from functools import partial
from toolz.dicttoolz import assoc
from random import sample, randrange
from html import unescape
from enum import Enum
from helpers import get_verdict, make_qr_code
from timer import Timer
from gameserver import MQTTGameServer
from constants import BACKENDS, SECS_PER_QUESTION, MULTIPLAYER_GAME_PATTERN, MULTIPLAYER_JOIN_LINK_BASE

import json

BUTTON_ORDER = ['red', 'green', 'yellow', 'blue']

class Player(EventDispatcher):

    game = ObjectProperty(rebind=True)
    name = StringProperty()
    id = StringProperty()
    total_score = BoundedNumericProperty(0, min=0)
    current_round = DictProperty(rebind=True)
    all_rounds = ListProperty([], rebind=True)
    answered = BooleanProperty(False)

    @staticmethod
    def get_new_round_dictionary(initial_score=0):
        return {'score': initial_score, 'verdict': None, 'position': None, 'answers': []}

    def __init__(self, game, name, id, initial_score=0, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_answer')
        self.register_event_type('on_correct_answer')
        self.register_event_type('on_incorrect_answer')
        self.register_event_type('on_already_answered')
        self.register_event_type('on_not_accepted')
        self.register_event_type('on_timed_out')
        self.game = game
        self.name = name
        self.id = id
        self.current_round = self.get_new_round_dictionary(initial_score)

    def on_answer(self):
        """Event handler for any accepted answer."""
        pass

    def on_correct_answer(self):
        """Event handler for correct answer."""
        self.dispatch('on_answer')

    def on_incorrect_answer(self):
        """Event handler for incorrect answer."""
        self.dispatch('on_answer')

    def on_already_answered(self):
        """Event handler for trying to answer when already answered."""
        pass

    def on_not_accepted(self):
        """Event handler for not accepted answer."""
        pass

    def on_timed_out(self):
        """Event handler for timed out answer."""
        pass

    def inc_score(self):
        """Increase score of current round."""
        self.current_round['score'] += 1

    def dec_score(self):
        """Decrease score of current round."""
        if self.current_round['score'] > 0:
            self.current_round['score'] -= 1

    def answer(self, answer_colour, from_button=False):
        """Handle player's answer."""
        if not self.answered:
            result = self.game.handle_answer(self, answer_colour, from_button)
            if result['accepted']:
                self.answered = True
                self.current_round['answers'].append(result['real_answer'])
                if result['correct_answer']:
                    self.dispatch('on_correct_answer')
                else:
                    self.dispatch('on_incorrect_answer')
            else:
                self.dispatch('on_not_accepted')
        else:
            self.dispatch('on_already_answered')

    def clean_answer_flag(self):
        """Allows player to input next answer."""
        self.answered = False

    def timed_out(self):
        """Called when a player hasn't answered in time."""
        self.answered = True
        self.current_round['answers'].append(False)
        self.dispatch('on_timed_out')

    def fetch_verdict(self):
        """Called when the current game has ended and the player's verdict has to be fetched."""
        self.current_round['verdict'] = get_verdict(self.current_round['score'] / len(self.current_round['answers']))

    def set_position(self, position):
        """Sets highscore position for current round."""
        self.current_round['position'] = position

    def next_round(self):
        """Archives current round and sets up next round."""
        self.total_score += self.current_round['score']
        self.all_rounds.append(self.current_round)
        self.current_round = self.get_new_round_dictionary()
        self.answered = False

class TriviaStates(Enum):
    STOPPED = 0
    JOINING = 1
    FETCHING = 2
    READY = 3
    RUNNING = 4
    FINISHED = 5
    CANCELLED = 7

class Trivia(EventDispatcher):
    """Trivia class"""

    current_state = ObjectProperty(TriviaStates.STOPPED)
    fetched = BooleanProperty(False)
    score = NumericProperty(0)
    round = NumericProperty(1)
    total_rounds = NumericProperty()
    game_number = NumericProperty(1)
    running = BooleanProperty(False)
    players = ListProperty([])
    player_count = NumericProperty(0)
    all_questions = ListProperty([])
    current_question = DictProperty(rebind=True)
    transitioning = BooleanProperty(False)
    timer = ObjectProperty(rebind=True)
    game_code = StringProperty()
    qr_code = ObjectProperty(rebind=True)

    def __init__(self, use_sample_data=False, **kwargs):
        super().__init__(**kwargs)
        # Events corresponding 1-to-1 to state changes
        self.register_event_type('on_stopped')
        self.register_event_type('on_joining')
        self.register_event_type('on_fetching')
        self.register_event_type('on_ready')
        self.register_event_type('on_running')
        self.register_event_type('on_finished')
        self.register_event_type('on_cancelled')
        # Convenience events
        self.register_event_type('on_ended')
        self.register_event_type('on_successful_join')
        self.register_event_type('on_illegal_join')
        self.register_event_type('on_correct_answer')
        self.register_event_type('on_incorrect_answer')
        self.register_event_type('on_timedout_answer')
        self.register_event_type('on_answer')
        self.register_event_type('on_all_answers')
        self.req = None
        self.use_sample_data = use_sample_data
        self.timer = Timer()
        self.server = MQTTGameServer(self)
        self.token = None

    def on_stopped(self):
        """Event handler for game stop."""
        pass

    def on_joining(self):
        """Event handler for game joining period."""
        App.get_running_app().goto_screen(s_name='joining', menu_mode=False)

    def on_fetching(self):
        """Event handler for when game is still fetching questions from API."""
        App.get_running_app().goto_screen(s_name='fetching', menu_mode=False)

    def on_ready(self):
        """Event handler for when game is ready to start."""
        pass

    def on_running(self):
        """Event handler for game start."""
        App.get_running_app().goto_screen(s_name='game', menu_mode=False)
        self.toggle_timer(start=True, reset=True)

    def on_finished(self):
        """Event handler for game finish."""
        self.dispatch('on_ended')

    def on_cancelled(self):
        """Event handler for game end due to cancellation."""
        self.dispatch('on_ended')

    def on_ended(self):
        """Event handler for game end for any reason."""
        all_scores = list(map(lambda player: player.current_round['score'], self.players))
        for player in self.players:
            player.fetch_verdict()
            player.set_position(self.get_players_position(all_scores, player))
            player.next_round()

    def get_players_position(self, all_scores, player):
        """Fetch a player's position in the current round."""
        all_scores.sort(reverse=True)
        print('All scores: {}'.format(all_scores))
        print('this score: {}'.format(player.current_round['score']))
        print('pos: {}'.format(all_scores.index(player.current_round['score'])))
        return all_scores.index(player.current_round['score']) + 1

    def on_successful_join(self):
        """Event handler for successful player join."""
        pass

    def on_illegal_join(self):
        """Event handler join attempt outside join state."""
        pass

    def on_answer(self, answer_colour, real_answer, from_button):
        """Event handler an answer, correct or incorrect, by any player."""
        pass

    def on_correct_answer(self, answer_colour, real_answer, from_button):
        """Event handler a correct answer by any player."""
        self.dispatch('on_answer', answer_colour, real_answer, from_button)

    def on_incorrect_answer(self, answer_colour, real_answer, from_button):
        """Event handler an incorrect answer by any player."""
        self.dispatch('on_answer', answer_colour, real_answer, from_button)

    def on_timedout_answer(self):
        """Event handler for answer timeout (at least 1 player has not answered)."""
        self.answer_timeout()

    def on_all_answers(self):
        """Event handler for change in players list."""
        self.transitioning = True
        self.next_round()

    def on_players(self, widget, new_players):
        """Event handler for change in players list."""
        self.player_count = len(new_players)

    def toggle_timer(self, start=True, reset=True):
        if start and App.get_running_app().opt_timer:
            self.timer.start_timer(SECS_PER_QUESTION, lambda: self.dispatch('on_timedout_answer'), windup=True, reset=reset)
        if not start and App.get_running_app().opt_timer:
            self.timer.halt_timer()

    def on_round(self, widget, new_round):
        """Advance current question."""
        if 1 <= new_round <= len(self.all_questions):
            # Checking for state to prevent timer going off when loading next game when score is still at the old last round
            if self.current_state == TriviaStates.RUNNING and new_round > 1:
                self.toggle_timer(start=True, reset=False)
            self.current_question = self.all_questions[new_round - 1]

    def on_timeout(self):
        """Event handler for game timer timeout"""
        self.current_state = TriviaStates.TIMEDOUT

    def on_current_state(self, widget, new_state):
        """State change handler."""
        self.dispatch('on_{}'.format(new_state.name.lower()))
        if new_state == TriviaStates.FINISHED or new_state == TriviaStates.CANCELLED:
            self.toggle_timer(False)

    def on_all_questions(self, widget, new_questions):
        """Refresh question count."""
        self.total_rounds = len(new_questions)
        self.property('round').dispatch(self)   # Because round was set to 1 when questions where not there yet. Should be handled better.

    def new_game(self, continuation=False):
        api = App.get_running_app().opt_api
        difficulty = App.get_running_app().opt_difficulty
        category = App.get_running_app().opt_category
        amount = App.get_running_app().opt_amount
        q_type = App.get_running_app().opt_type
        multiplayer = App.get_running_app().opt_multiplayer

        self.transitioning = False
        self.fetched = False
        self.check_token_and_fetch_new(api, difficulty, category, amount, q_type)
        if continuation:
            self.current_state = TriviaStates.FETCHING
            self.start_game()
        else:
            self.players.clear()
            if multiplayer:
                # TODO: Make random again / improve
                self.game_code = MULTIPLAYER_GAME_PATTERN.format(randrange(0, 11, 1))
                self.qr_code = make_qr_code(MULTIPLAYER_JOIN_LINK_BASE, self.game_code)
                self.server.listen(self.game_code)
                print('Multiplayer game with code {} started'.format(self.game_code))

                self.current_state = TriviaStates.JOINING
            else:
                self.add_player('feduquiz-0', 'Player 1', True)
                self.current_state = TriviaStates.FETCHING
                self.start_game()

    def add_player(self, name, id, force_add=False):
        """Lets a new player join the game."""
        print('Player join request for player {} with id {}'.format(name, id))
        if force_add or self.current_state == TriviaStates.JOINING:
            new_player = Player(self, name, id)
            if not self.does_player_exist(new_player):
                self.players.append(new_player)
                return new_player
            else:
                print('Player {} with id {} already exists.'.format(name, id))
                return False
        else:
            print('Player {} with id {} tried to join game outside of joining window.'.format(name, id))
            return False

    def clean_player_answer_flags(self):
        for player in self.players:
            player.clean_answer_flag()

    def start_game(self, dt=None):
        """Closes the joining period to start the game."""
        if not self.fetched:
            self.current_state = TriviaStates.FETCHING
            Clock.schedule_once(self.start_game)
        else:
            self.current_state = TriviaStates.RUNNING
            self.game_number = 1
            self.score = 0
            self.round = 1

    def next_round(self):
        if self.current_state == TriviaStates.RUNNING:
            if self.round >= len(self.all_questions):
                self.current_state = TriviaStates.FINISHED
            else:
                self.clean_player_answer_flags()
                self.round += 1

    def single_player_answer(self, answer_colour):
        """Convenience function that passes through the answer from buttons in single-player mode only."""
        if not App.get_running_app().opt_multiplayer:
            self.players[0].answer(answer_colour, True)

    def handle_answer(self, player, answer_colour, from_button=False):
        if self.current_state == TriviaStates.RUNNING and not self.transitioning:
            selected_answer = self.get_answer_from_button_color(answer_colour)
            if not selected_answer:
                return { 'accepted': False }
            if self.current_question['correct_answer'] == selected_answer:
                player.inc_score()
                answer_result = True
                self.dispatch('on_correct_answer', answer_colour, selected_answer, from_button)
            else:
                answer_result = False
                self.dispatch('on_incorrect_answer', answer_colour, selected_answer, from_button)
            Clock.schedule_once(lambda dt: self.conditional_dispatch_all_answered())
            return { 'accepted': True, 'correct_answer': answer_result, 'real_answer': selected_answer }
        else:
            return { 'accepted': False }

    def answer_timeout(self):
        """Called when the timeout is over."""
        if self.current_state == TriviaStates.RUNNING and not self.transitioning:
            players_without_answer = self.get_players_without_answer()
            for player in players_without_answer:
                player.timed_out()
            Clock.schedule_once(lambda dt: self.conditional_dispatch_all_answered())

    def conditional_dispatch_all_answered(self):
        """Checks if all answers have been provided. If so, dispatches corresponding event."""
        if self.check_if_all_answers_provided():
            self.dispatch('on_all_answers')

    def get_answer_from_button_color(self, answer_colour):
        """Takes the button colour as input and return the actual answer."""
        button_index = BUTTON_ORDER.index(answer_colour)
        if len(self.current_question['shuffled_answers']) > button_index:
            return self.current_question['shuffled_answers'][BUTTON_ORDER.index(answer_colour)]
        else:
            return False

    def check_if_all_answers_provided(self):
        """Check if answers from all players have been received."""
        return all(player.answered for player in self.players)

    def get_players_without_answer(self):
        """Returns all players that haven't answered yet."""
        return filter(lambda player: player.answered == False, self.players)

    def does_player_exist(self, player):
        """Checks if the given player id (or name) is already in use."""
        new_player_has_same_id_or_name_as = lambda curr_player: curr_player.id == player.id or curr_player.name == player.name
        return any(new_player_has_same_id_or_name_as(existing_player) for existing_player in self.players)

    def end_transitioning(self):
        """Used to notify that relevant animations are done and answers can be accepted."""
        self.transitioning = False

    def check_token_and_fetch_new(self, api, difficulty, category, amount, q_type):
        if not self.token and "token" in BACKENDS[api]:
            UrlRequest(
                BACKENDS[api]['token'],
                on_success=partial(self.save_token_and_fetch_new, api, difficulty, category, amount, q_type),
                on_failure=self.fetch_fail,
                on_error=self.fetch_error
            )
        else:
            self.fetch_new(api, difficulty, category, amount, q_type)

    def save_token_and_fetch_new(self, api, difficulty, category, amount, q_type, request, result):
        self.token = result['token']
        self.fetch_new(api, difficulty, category, amount, q_type)

    def fetch_new(self, api, difficulty, category, amount, q_type):
        if self.use_sample_data:
            import json
            with open('./resources/sample_quiz_data.json') as f:
                data = json.load(f)
            self.fetch_success(None, data)
        else:
            base_url = BACKENDS[api]['url'] + '?'
            if self.token:
                base_url += 'token=' + str(self.token) + '&'
            if difficulty is not '':
                base_url += 'difficulty=' + str(difficulty) + '&'
            if category is not 0:
                base_url += 'category=' + str(category) + '&'
            if q_type is not '':
                base_url += 'type=' + str(q_type) + '&'
            base_url += 'amount=' + str(amount)
            self.req = UrlRequest(
                base_url,
                on_success=partial(self.fetch_success, api, difficulty, category, amount, q_type),
                on_failure=self.fetch_fail,
                on_error=self.fetch_error
            )

    def fetch_success(self, api, difficulty, category, amount, q_type, request, result):
        if result['response_code'] == 3 or result['response_code'] == 4:
            print("Token invalidated, fetching again ...")
            self.token = None
            return self.check_token_and_fetch_new(api, difficulty, category, amount, q_type)
        self.all_questions = self.shuffle_answers(self.html_decode(result['results']))
        #self.current_state = TriviaStates.RUNNING
        self.fetched = True
        try:
            print(self.all_questions)
            print()
        except:
            # Probably a unicode error.
            print("Could not print quiz data.")

    def fetch_fail(self, request, result):
        print("Failure fetching quiz data: {}".format(result))

    def fetch_error(self, request, error):
        print("Error fetching quiz data: {}".format(error))

    @staticmethod
    def shuffle_answers(questions):
        """Adds a key to each question containing the shuffled answers (correct and incorrect), or unshuffled for True/False"""
        shuffle_answers = lambda answers: sample(answers, len(answers)) if len(answers) > 2 else ['True', 'False']
        assoc_shuffled_answers = lambda question: assoc(question, 'shuffled_answers', shuffle_answers([question['correct_answer']] + question['incorrect_answers']))

        return map(assoc_shuffled_answers, questions)

    @staticmethod
    def html_decode(quiz_obj):
        """
        URL decodes or unencodes the quiz data recursively.
        Credits to https://nvie.com/posts/modifying-deeply-nested-structures/
        """
        if isinstance(quiz_obj, dict):
            return {k: Trivia.html_decode(v) for k, v in quiz_obj.items()}
        elif isinstance(quiz_obj, list):
            return [Trivia.html_decode(elem) for elem in quiz_obj]
        else:
            return unescape(quiz_obj)

