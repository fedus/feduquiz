#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty, ObjectProperty

from random import choice
from functools import partial

from helpers import get_verdict
from simple_widgets import MainTitle
from trivia import TriviaStates
from constants import CEC_CMD_MAP, NEGATIVES, POSITIVES

import sys

DELAY_START = True if '--delay-start' in sys.argv else False


class TitleScreen(Screen):

    # Title_text is the string used to populate the MainTitle of the TitleScreen
    title_text = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_pre_enter(self):
        self.reset_widgets()

    def on_enter(self):
        """
        Starts animating in the MainTitle, and attches a callback to the animation
        to method "start_secondary_anims". The latter will then fade in the rest of the
        widgets one by one.
        """
        if self.title_text:
            anim = Animation(scale=1, opacity=1, t='out_elastic', duration=1)
            anim.bind(on_complete=partial(self.start_secondary_anims, direction='in'))
            anim.start(self.ids.main_title)
        else:
            self.start_secondary_anims(None, None, direction='in')

    def start_secondary_anims(self, anim, widget, direction):
        """
        Sequentially fades in all widgets except for the MainTitle (which is already visible
        by now).
        """
        if direction == 'in':
            fade_func = self.fade_in_widget
        else:
            fade_func = self.fade_out_widget
        delay = 0
        for child in reversed(self.children):
            if (type(child) is MainTitle and direction == 'in') or not child.auto_anim:
                # This is the MainTitle, which is already visible and should be skipped here.
                continue
            Clock.schedule_once(partial(fade_func, child), delay)
            delay += 0.1
        return delay

    def fade_in_widget(self, widget, dt=None):
        """Fades in the given widget."""
        Animation(opacity=1, duration=0.5).start(widget)

    def fade_out_widget(self, widget, dt=None):
        """Fades in the given widget."""
        Animation(opacity=0, duration=0.5).start(widget)

    def reset_widgets(self):
        """Resets all widgets to their pre-animation state."""
        self.ids.main_title.scale = 0
        for child in self.children:
            if child.auto_anim:
                child.opacity = 0

    def goto_func(self, func):
        """
        Leave this screen by fading out all widgets and executing func()
        The latter is a method which should result in a screen switch.
        """
        next_delay = self.start_secondary_anims(None, None, direction='out')
        Clock.schedule_once(lambda dt: func(), next_delay+0.1)

class Intro(Screen):

    outline_col = ListProperty([0.4, 0, 0.9])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.outline_anim = None
        self.press_ok_anim2 = None
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "intro", partial(self.goto_screen, "game"))
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "intro", partial(self.goto_screen, "options"))

    def on_enter(self):
        """"
        The --delay-start argument can delay the start of the application (and thus animations).
        This allows for easy screen recording, for example.
        """
        if not DELAY_START:
            self.opening_animations()

    def on_touch_down(self, touch):
        """"
        The --delay-start argument can delay the start of the application (and thus animations).
        This allows for easy screen recording, for example.
        Clicking on the screen starts the app in this case.
        """
        if DELAY_START:
            self.opening_animations()
        return super(Intro, self).on_touch_down(touch)

    def opening_animations(self):
        App.get_running_app().bg_anim.start(App.get_running_app())
        anim = Animation(scale=1, opacity=1, t='out_elastic', duration=2)
        anim.bind(on_complete=self.start_secondary_anims)
        anim.start(self.ids.feduquiz_title)

    def start_secondary_anims(self, anim=None, widget=None):
        self.outline_anim = (Animation(outline_col=[0.9,0,0], duration=2) +
                        Animation(outline_col=[0.9,0.9,0], duration=2) +
                        Animation(outline_col=[0, 0.9, 0.9], duration=2) +
                        Animation(outline_col=[0, 0, 0.9], duration=2) +
                        Animation(outline_col=[0.9, 0, 0.9], duration=2))
        self.outline_anim.repeat = True

        self.press_ok_anim2 = Animation(opacity=0.5) + Animation(opacity=1)
        self.press_ok_anim2.repeat = True

        press_ok_anim1 = Animation(pos_hint={'center_x': 0.5, 'center_y': 0.35}, opacity=1, t='out_circ', duration=1)
        press_ok_anim1.bind(on_complete=lambda anim,widget: self.press_ok_anim2.start(self.ids.press_ok))
        press_ok_anim1.start(self.ids.press_ok)

        move_title_anim = Animation(pos_hint={'center_x': 0.5, 'center_y': 0.6}, t='out_circ', duration=1)
        move_title_anim.bind(on_complete=lambda anim, widget: self.outline_anim.start(self))
        move_title_anim.start(self.ids.feduquiz_title)

    def goto_screen(self, screen):
        self.outline_anim.cancel(self.ids.feduquiz_title)
        self.press_ok_anim2.cancel(self.ids.press_ok)
        anim1 = Animation(opacity=0)
        anim2 = Animation(opacity=0)
        if screen == "game":
            anim2.bind(on_complete=lambda widget, anim: App.get_running_app().trivia.new_game())
        if screen == "options":
            anim2.bind(on_complete=partial(self.set_screen, "options"))
        anim1.start(self.ids.feduquiz_title)
        anim2.start(self.ids.press_ok)

    def set_screen(self, screen, anim=None, widget=None):
        # Should be done using App's method!
        if screen == "options":
            App.get_running_app().snd_machine.mode_menu()
        else:
            App.get_running_app().snd_machine.mode_game()
        self.manager.current = screen

class Options(TitleScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["UP"], "options", self.ids.menu.focus_prev)
        App.get_running_app().add_callback(CEC_CMD_MAP["DOWN"], "options", self.ids.menu.focus_next)
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "options", lambda: self.ids.menu.get_focus_current().trigger_action())
        App.get_running_app().add_callback(CEC_CMD_MAP["RIGHT"], "options", lambda: self.ids.menu.get_focus_current().option_next())
        App.get_running_app().add_callback(CEC_CMD_MAP["LEFT"], "options", lambda: self.ids.menu.get_focus_current().option_prev())

class Instructions(TitleScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "instructions", partial(App.get_running_app().goto_screen, s_name='options'))

class Credits(TitleScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "credits", partial(App.get_running_app().goto_screen, s_name='options'))

class Game(Screen):

    trivia = ObjectProperty(rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "game", lambda: self.ids.game_buttons.ids.btn_red.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["GREEN"], "game", lambda: self.ids.game_buttons.ids.btn_green.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["YELLOW"], "game", lambda: self.ids.game_buttons.ids.btn_yellow.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["BLUE"], "game", lambda: self.ids.game_buttons.ids.btn_blue.trigger_action(duration=.1))

        self.btn_pressed_anim = Animation(scale=1.1, duration=0.1) + Animation(scale=1, duration=0.1)
        self.last_q_anim_direction = None

        self.last_button_color = None

        self.ids.info_widget.ids.timer_bar.link_timer(self.trivia.timer)
        self.trivia.bind(on_timedout_answer=lambda widget: self.timeout_sequence())
        self.trivia.bind(on_answer=lambda widget, answer_colour, real_answer, from_button: self.button_press(answer_colour, from_button))
        self.trivia.bind(round=lambda widget, round_number: self.next_round_sequence(round_number))
        self.trivia.bind(on_correct_answer=lambda widget, answer_colour, real_answer, from_button: self.answer_sequence('correct'))
        self.trivia.bind(on_incorrect_answer=lambda widget, answer_colour, real_answer, from_button: self.answer_sequence('incorrect'))
        self.trivia.bind(on_ended=lambda widget: self.anim_out(True))

    def on_enter(self, *args):
        App.get_running_app().snd_machine.mode_game()
        self.gi_anim("in")
        self.q_anim("in")
        self.ids.game_buttons.anim_all("in")

    def button_press(self, color, from_button=False):
        if not App.get_running_app().opt_multiplayer:
            if not from_button:
                self.ids.game_buttons.ids['btn_{}'.format(color)].trigger_action(duration=.1)
            self.ids.game_buttons.ids.game_btn_layout.remove_widget(self.ids.game_buttons.ids['btn_'+color])
            self.ids.game_buttons.ids.game_btn_layout.add_widget(self.ids.game_buttons.ids['btn_'+color])
            self.btn_pressed_anim.start(self.ids.game_buttons.ids['btn_'+color])
            print("BUTTON PRESS: " + color)
            self.last_button_color = color
        else:
            self.btn_pressed_anim.start(self.ids.game_buttons)
            self.last_button_color = None

    def timeout_sequence(self):
        self.ids.negative_label.text = 'Too late!'
        Clock.schedule_once(lambda dt: self.ids.negative_label.animate(), 0.5)

    def answer_sequence(self, answer_result):
        """Animates the answer feedback label."""
        if answer_result == 'correct':
            print("CORRECT ANSWER")
            sound_feedback = 'correct'
            feedback_msg = choice(POSITIVES)
            feedback_lbl = self.ids.positive_label
        elif answer_result == 'incorrect':
            print("WRONG ANSWER")
            sound_feedback = 'wrong'
            feedback_msg = choice(NEGATIVES)
            feedback_lbl = self.ids.negative_label

        # Animate answer feedback
        feedback_lbl.text = feedback_msg
        if App.get_running_app().opt_instant_fb:
            Clock.schedule_once(lambda dt: feedback_lbl.animate(), 0.3)
        else:
            sound_feedback = 'neutral'

        App.get_running_app().snd_machine.btn_answer(sound_feedback)

    def next_round_sequence(self, round_number):
        """Animation for transitioning to next round."""
        # For the first round, the controls are already there
        if self.last_q_anim_direction == 'in':
            self.anim_out()

    def anim_out(self, game_end=False):
            self.q_anim("out")
            self.ids.game_buttons.anim_all("out", highlight=self.last_button_color, callback=lambda: self.anim_in_or_end(game_end))

    def anim_in_or_end(self, game_end=False):
        # Reset positions of question label and input buttons
        self.ids.game_buttons.reset_pos()

        if game_end:
            #Game is over, move to highscores
            self.gi_anim("out")
            Clock.schedule_once(self.goto_score, 1)
        else:
            # Bring back question label and input buttons
            self.q_anim("in")
            self.ids.game_buttons.anim_all("in")
            self.trivia.end_transitioning()

    def goto_score(self, dt=None):
        self.manager.current = 'score'

    def q_anim(self, direction):
        self.last_q_anim_direction = direction
        if direction == "in":
            self.ids.question_label.anim_in()
        else:
            self.ids.question_label.anim_out()

    def gi_anim(self, direction):
        if direction == "in":
            anim = Animation(
                pos_hint={'center_x': self.ids.info_widget.primary_position[0],
                          'top': self.ids.info_widget.primary_position[1]},
                opacity=1,
                t='out_elastic',
                duration=0.5)
        else:
            anim = Animation(
                pos_hint={'center_x': self.ids.info_widget.secondary_position[0],
                          'top': self.ids.info_widget.secondary_position[1]},
                opacity=0,
                t='in_back',
                duration=0.5)
        anim.start(self.ids.info_widget)

class Score(TitleScreen):

    player = ObjectProperty(rebind=True)
    #player2 = ObjectProperty(rebind=True)
    top_three = ObjectProperty(rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.press_ok_anim2 = None
        self.out_anim_1 = None
        self.out_anim_2 = None
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "score", lambda: App.get_running_app().trivia.new_game(continuation=True))
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "score", partial(App.get_running_app().goto_screen, s_name='options'))

    def start_secondary_anims(self, anim, widget, direction):
        if direction == 'in':
            # The "Press OK" label is animated manually, because it has a special fade-in
            # animation. However, we want it to fade out just like the other widgets. Hence,
            # we set auto_anim to True after it has been animated it. Later, we override the
            # reset_widgets function to set auto_anim back to False after calling super's
            # reset_widgets.
            self.press_ok_anim2 = Animation(opacity=1) + Animation(opacity=0.5)
            self.press_ok_anim2.repeat = True
            Clock.schedule_once(lambda dt: self.press_ok_anim2.start(self.ids.press_ok), 0.2)
        else:
            self.ids.press_ok.auto_anim = True
            self.press_ok_anim2.cancel(self.ids.press_ok)
        return super().start_secondary_anims(anim, widget, direction)

    def reset_widgets(self):
        # See explanation above
        super().reset_widgets()
        self.ids.press_ok.auto_anim = False

    def on_pre_enter(self):
        self.top_three.sort_and_render()
        super().on_pre_enter()

class Fetching(TitleScreen):
    pass

class Joining(TitleScreen):

    players = ListProperty([])
    waiting = ObjectProperty(rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "joining", App.get_running_app().trivia.start_game)
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "joining", partial(App.get_running_app().goto_screen, s_name='options'))

    def on_players(self, widget, players):
        if len(players):
            Animation(opacity=0, duration=0.1).start(self.waiting)
        else:
            Animation(opacity=1, duration=0.1).start(self.waiting)
