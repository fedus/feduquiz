#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty

from random import shuffle, choice
from functools import partial

from helpers import get_verdict
from simple_widgets import MainTitle
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
        anim = Animation(scale=1, opacity=1, t='out_elastic', duration=1)
        anim.bind(on_complete=partial(self.start_secondary_anims, direction='in'))
        anim.start(self.ids.main_title)
        
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
        Clock.schedule_once(func, next_delay+0.1)

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
            anim2.bind(on_complete=App.get_running_app().load_game)
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
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "instructions", partial(self.goto_func, partial(App.get_running_app().goto_screen, s_name='options')))

class Credits(TitleScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "credits", partial(self.goto_func, partial(App.get_running_app().goto_screen, s_name='options')))

class Game(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "game", lambda: self.ids.game_buttons.ids.btn_red.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["GREEN"], "game", lambda: self.ids.game_buttons.ids.btn_green.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["YELLOW"], "game", lambda: self.ids.game_buttons.ids.btn_yellow.trigger_action(duration=.1))
        App.get_running_app().add_callback(CEC_CMD_MAP["BLUE"], "game", lambda: self.ids.game_buttons.ids.btn_blue.trigger_action(duration=.1))

        self.btn_pressed_anim = Animation(scale=1.1, duration=0.1) + Animation(scale=1, duration=0.1)

        self.answer = None
        self.buttons_active = False
        self.last_button_color = None

    def on_enter(self, *args):
        self.load_current_question()
        self.gi_anim("in")
        self.q_anim("in")
        self.ids.game_buttons.anim_all("in")
        self.buttons_active = True

    def load_current_question(self):
        if App.get_running_app().trivia.check_game():
            current_question = App.get_running_app().trivia.get_current_question()
            App.get_running_app().curr_question = current_question["question"]
            App.get_running_app().curr_author = current_question["author"] if "author" in current_question else ''
            App.get_running_app().curr_type = current_question["type"]
            App.get_running_app().curr_difficulty = current_question["difficulty"]
            App.get_running_app().curr_category = current_question["category"]
            App.get_running_app().curr_correct = current_question["correct_answer"]
            App.get_running_app().curr_wrong = current_question["incorrect_answers"]
            App.get_running_app().curr_round = App.get_running_app().trivia.get_current_round()
            App.get_running_app().curr_total_rounds = App.get_running_app().trivia.get_total_rounds()
            self.shuffle_btn_labels(App.get_running_app().curr_correct, App.get_running_app().curr_wrong)

    def shuffle_btn_labels(self, correct, base):
        base.append(correct)
        shuffle(base)
        App.get_running_app().curr_btn_labels.clear()
        for answer in base:
            App.get_running_app().curr_btn_labels.append(answer)


    def button_press(self, color):
        if self.buttons_active:
            self.ids.game_buttons.ids.game_btn_layout.remove_widget(self.ids.game_buttons.ids['btn_'+color])
            self.ids.game_buttons.ids.game_btn_layout.add_widget(self.ids.game_buttons.ids['btn_'+color])
            self.btn_pressed_anim.start(self.ids.game_buttons.ids['btn_'+color])
            print("BUTTON PRESS: " + color)
            self.answer = self.ids.game_buttons.ids['btn_'+color].text
            self.last_button_color = color
            self.start_answer_sequence()

    def timeout_sequence(self):
        self.buttons_active = False
        self.q_anim("out")

        App.get_running_app().trivia.cancel_game('timeout')

        self.ids.negative_label.text = 'Too late!'
        Clock.schedule_once(lambda dt: self.ids.negative_label.animate(), 0.5)

        self.ids.game_buttons.anim_all("out", highlight=self.last_button_color, callback=self.end_answer_sequence)
        App.get_running_app().snd_machine.mode_game(False)

    def start_answer_sequence(self):
        self.buttons_active = False
        self.q_anim("out")
        self.ids.game_buttons.anim_all("out", highlight=self.last_button_color, callback=self.end_answer_sequence)

        if self.answer == App.get_running_app().curr_correct:
            print("CORRECT ANSWER")
            sound_feedback = 'correct'
            feedback_msg = choice(POSITIVES)
            feedback_lbl = self.ids.positive_label
            App.get_running_app().trivia.register_answer(True)
        else:
            print("WRONG ANSWER")
            sound_feedback = 'wrong'
            feedback_msg = choice(NEGATIVES)
            feedback_lbl = self.ids.negative_label
            App.get_running_app().trivia.register_answer(False)

        # Animate answer feedback
        feedback_lbl.text = feedback_msg
        if App.get_running_app().opt_instant_fb:
            Clock.schedule_once(lambda dt: feedback_lbl.animate(), 0.3)
        else:
            sound_feedback = 'neutral'

        App.get_running_app().snd_machine.btn_answer(sound_feedback)

    def end_answer_sequence(self):
        # Reset positions of question label and input buttons
        self.q_reset_pos()
        self.ids.game_buttons.reset_pos()

        App.get_running_app().curr_score = App.get_running_app().trivia.score

        if App.get_running_app().trivia.check_game():
            # Game is still running - next question
            self.load_current_question()

            # Bring back question label and input buttons
            self.q_anim("in")
            self.ids.game_buttons.anim_all("in")
            self.buttons_active = True
        else:
            # Game has ended - move to highscores
            App.get_running_app().curr_author = '' # We want the author label to hide for the next game
            App.get_running_app().curr_verdict = get_verdict(App.get_running_app().curr_score / App.get_running_app().curr_total_rounds)
            self.gi_anim("out")
            Clock.schedule_once(self.goto_score, 1)

    def goto_score(self, dt=None):
        self.manager.current = 'score'

    def q_anim(self, direction):
        if direction == "in":
            anim = Animation(
                pos_hint={'center_x': self.ids.question_label.primary_position[0],
                          'center_y': self.ids.question_label.primary_position[1]},
                opacity=1,
                t='out_quad',
                duration=0.5)
            self.ids.question_label.anim_mask_open()
        else:
            anim = Animation(
                pos_hint={'center_x': self.ids.question_label.secondary_position_2[0],
                          'center_y': self.ids.question_label.secondary_position_2[1]},
                opacity=0,
                t='in_quad',
                duration=0.5)
            anim.bind(on_complete=self.ids.question_label.reset_pos)
        anim.start(self.ids.question_label)

    def q_reset_pos(self):
        self.ids.question_label.pos_hint = {
            'center_x': self.ids.question_label.secondary_position_1[0],
            'center_y': self.ids.question_label.secondary_position_1[1]
        }

    def gi_anim(self, direction):
        if direction == "in":
            anim = Animation(
                pos_hint={'center_x': self.ids.info_widget.primary_position[0],
                          'top': self.ids.info_widget.primary_position[1]},
                opacity=1,
                t='out_elastic',
                duration=0.5)
            if App.get_running_app().opt_timer:
                self.ids.info_widget.ids.timer_bar.start_timer(App.get_running_app().curr_total_rounds, self.timeout_sequence)
        else:
            anim = Animation(
                pos_hint={'center_x': self.ids.info_widget.secondary_position[0],
                          'top': self.ids.info_widget.secondary_position[1]},
                opacity=0,
                t='in_back',
                duration=0.5)
            if App.get_running_app().opt_timer:
                self.ids.info_widget.ids.timer_bar.halt_timer()
        anim.start(self.ids.info_widget)

class Score(TitleScreen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.press_ok_anim2 = None
        self.out_anim_1 = None
        self.out_anim_2 = None
        App.get_running_app().add_callback(CEC_CMD_MAP["OK"], "score", partial(self.goto_func, App.get_running_app().load_game))
        App.get_running_app().add_callback(CEC_CMD_MAP["RED"], "score", partial(self.goto_func, partial(App.get_running_app().goto_screen, s_name='options')))

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
