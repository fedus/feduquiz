#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.graphics import Color
from time import sleep
from kivy.logger import Logger
from kivy.clock import Clock, mainthread
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.effectwidget import EffectWidget
from kivy.animation import Animation
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.properties import NumericProperty, ListProperty, StringProperty, BooleanProperty, ObjectProperty, DictProperty
from kivy.graphics.opengl import *
from kivy.graphics import *

from random import shuffle, choice, randint
from functools import partial

from helpers import get_categories, get_verdict
from trivia import Trivia
from soundmachine import SoundMachine
from screens import TitleScreen, Intro, Options, Instructions, Credits, Game, Score
from constants import CEC_CMD_MAP, TRIVIA_URL, INSTRUCTION_TEXT

import json
import sys


# Pass cli arguments

DISABLE_CEC = True if '--disable-cec' in sys.argv else False
USE_SAMPLE_DATA = True if '--use-sample-data' in sys.argv else False
SET_SIZE = True if '--set-size' in sys.argv else False


class ScrollMenu(BoxLayout):

    menu_width = NumericProperty()
    items_per_page = NumericProperty()
    indicator_center_y = NumericProperty()
    
    def add_widget(self, widget):
        """
        Forwards widgets to the FreeScrollView after the OptionIndicator and FreeScrollView
        have been added.
        """
        if len(self.children) < 2:
            super().add_widget(widget)
        else:
            self.ids.free_scroll_view.add_widget(widget)

    def get_focus_current(self):
        return self.ids.free_scroll_view.current_focus

    def focus_next(self):
        self.ids.free_scroll_view.current_focus.get_focus_next().focus = True
    
    def focus_prev(self):
        self.ids.free_scroll_view.current_focus.get_focus_previous().focus = True

class AlphaWidget(EffectWidget):

    def __init__(self, **kwargs):
        super(AlphaWidget, self).__init__(**kwargs)
        with self.canvas.before:
            Callback(self._set_blend_func)
        with self.canvas.after:
            # Hacky way to make sure Kivy restores the GL context in line with its
            # requirements.
            Callback(self._reset_blend_func, reset_context=True)

    def _set_blend_func(self, instruction):
        """
        Sets the correct OpenGL blend mode.
        This distorts Kivy's OpenGL context and we must ensure that it is restored.
        """
        glBlendFunc(GL_SRC_ALPHA, GL_DST_ALPHA)

    def _reset_blend_func(self, instruction):
        """Dummy function."""
        pass

class FreeScrollView(ScrollView):

    items_per_page = NumericProperty()
    padding = NumericProperty()
    spacing = NumericProperty()
    indicator_center_y = NumericProperty()
    current_focus = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicator_anim = Animation()
        self.wait_for_widget = False

    def percentage_visible(self, widget):
        """
        Returns a float between 0. and 1. indicating how much of a given
        widget is visible within the ScrollView.
        Currently only implemented relative to a widget's HEIGHT.
        """
        widget_xy = self.to_parent(widget.x, widget.y, relative=False)
        widget_tr = self.to_parent(widget.right, widget.top, relative=False)

        if widget_xy[1] < self.y:
            opacity = (((widget_xy[1]+widget.height)-self.y)/widget.height) if widget.height > 0 else 0
            return opacity
        elif widget_tr[1] > self.top:
            opacity = ((self.top-widget_xy[1])/widget.height) if widget.height > 0 else 0
            return opacity
        return 1
        
    def on_scroll_y(self, *args):
        """
        Prompts the BoxLayout contained within the FreeScrollView to
        walk through its children and adapt their opacity.
        """
        #print("Scroll y  {}".format(str(args)))
        self.ids.saware_layout.do_bound_check()
        Clock.schedule_once(self.await_focus_widget)
    
    def await_focus_widget(self, dt=None):
        if self.wait_for_widget:
            if self.percentage_visible(self.current_focus) == 1:
                self.wait_for_widget = False
                Clock.schedule_once(self.set_indicator_y, 0.05)
                
    
    def add_widget(self, widget):
        """
        Allows the addition of one widget to the FreeScrollView, which will be the
        ScrollAwareLayout. After this, every widget addition is forwarded to the ScrollAwareLayout.
        """
        if len(self.children) == 0:
            print("Adding widget to FreeScrollView. Widget {}".format(widget))
            super().add_widget(widget)
        else:
            print("Forwarding widget addition to ScrollAwareLayout. Widget {}".format(widget))
            self.ids.saware_layout.add_widget(widget)

    def get_relative_center_y(self, widget):
        """
        Gets the current center_y position of the currently focussed
        OptionButton, relative to the whole ScrollMenu.
        """
        
        # For convenience, get the widget's absolute y position
        widget_y = self.to_parent(self.current_focus.center_x, self.current_focus.center_y)[1]
        
        # Calculate at what "height" of the ScrollView the widget is situated
        widget_pos_in_parent = widget_y - self.y
        
        # Divide the current "height" of the widget in the ScrollView by the ScrollView's
        # height to find its relative position and call animation method of parent.
        rel_pos = widget_pos_in_parent/self.height
        print("Relative center_y: {}".format(rel_pos))
        return rel_pos

    def set_indicator_y(self, dt=None):
        """Animates the"""
        y = self.get_relative_center_y(self.current_focus)
        self.animate_indicator(y)

    def animate_indicator(self, rel_y):
        """Animates self.indicator_center_y to rel_y"""
        self.indicator_anim.cancel(self)
        self.indicator_anim = Animation(indicator_center_y=rel_y, duration=0.1)
        self.indicator_anim.start(self)

    def on_current_focus(self, parent, widget):
        print("Current focus changed! {}".format(widget))
        Clock.schedule_once(self.check_for_indicator_animation)
        
    def check_for_indicator_animation(self, dt=None):
        percentage = self.percentage_visible(self.current_focus)
        if percentage < 1:
            print("WAITING {}".format(percentage))
            self.wait_for_widget = True
            self.scroll_to(self.current_focus, padding=10, animate={'duration': 0.1})
        else:
            print("NOT waiting")
            Clock.schedule_once(self.set_indicator_y)

class ScrollAwareLayout(BoxLayout):

    height_per_child = NumericProperty()
    current_focus = ObjectProperty()

    def on_height(self, *args):
        self.height_per_child = (self.height / len(self.children)) if len(self.children) > 0 else 0
        print("Height per child: {}".format(self.height_per_child))
        self.do_bound_check()

    def add_widget(self, widget):
        """Adding widget and checking what children are visible in parent FreeScrollView."""
        widget.size_hint = 1, None
        super().add_widget(widget)

    def do_bound_check(self, dt=None):
        """
        Schedules the boundary check for every child widget for the next frame.
        It seems to be necessary to wait for the next frame as final positions have not
        been reached at the time this method is called.
        """
        Clock.schedule_once(self.deferred_bound_check2)

    def deferred_bound_check2(self, dt=None):
        for child in self.children:
            child.opacity = self.parent.percentage_visible(child)

    def on_current_focus(self, parent, widget):
        """Percolate up the focus change."""
        self.parent.current_focus = widget


class RoundedBox(BoxLayout):
    pass

class PlayOrOptions(RoundedBox):
    pass

class GameButtons(Widget):

    game_root = ObjectProperty()

    def anim_all(self, direction, highlight=None, callback=None):

        # Check if we're animating in or out
        if direction == "in":
            anim_func = self.anim_in
        else:
            anim_func = self.anim_out

        # Set start timer to 0
        time_start = 0

        # Check what buttons need to be animated which way (to highlight answer)
        # Only really intended to be used for the fade OUT animation!
        col_list = ['red', 'green', 'yellow', 'blue'] if len(App.get_running_app().curr_btn_labels) > 2 else ['red', 'green']
        col_needed = [col for col in col_list if col is not highlight] if highlight else col_list
        
        # Check if a button is to be highlighted (ie
        if highlight:
            Animation(opacity=0, scale=1.5, duration=0.6).start(self.ids['btn_' + highlight])

        for index, color in enumerate(col_needed):

            # "Normal" animation
            if callback is None or index < (len(col_needed)-1):
                Clock.schedule_once(partial(anim_func, btn=self.ids['btn_' + color], callback=None), time_start)
            else:
                # We want to attach any potential callback to the last button animation
                Clock.schedule_once(partial(anim_func, btn=self.ids['btn_' + color], callback=callback), time_start)
            time_start += 0.1

        if direction == "in":
            for color in col_list:
                self.ids['btn_' + color].stop_effect_anims()
                Clock.schedule_once(self.ids['btn_' + color].effect_anim, 0.7)


    def test_func(self, *args, **kwargs):
        print('The flexible function has *args of', str(args),
            "and **kwargs of", str(kwargs))

    def anim_in(self, dt, btn, callback=None):
        anim = Animation(pos_hint={'center_x': btn.primary_position[0], 'center_y': btn.primary_position[1]}, scale=1,
                  t='out_elastic', duration=1)
        if callback:
            anim.bind(on_complete=lambda anim, widget: callback())
        anim.start(btn)

    def anim_out(self, dt, btn, callback=None):
        anim = Animation(pos_hint={'center_x': btn.secondary_position_2[0], 'center_y': btn.secondary_position_2[1]}, scale=btn.secondary_scale_2,
                  t='in_circ', duration=0.5)
        if callback:
            anim.bind(on_complete=lambda anim, widget: callback())
        anim.start(btn)

    def reset_pos(self):
        for color in ['red', 'green', 'yellow', 'blue']:
            btn = self.ids['btn_'+color]
            btn.opacity = 1
            btn.pos_hint = {'center_x': btn.secondary_position_1[0], 'center_y': btn.secondary_position_1[1]}
            btn.scale = btn.secondary_scale_2

class TriviaButton(Button):

    scale = NumericProperty()
    x_transform = NumericProperty()
    x_transform_end = NumericProperty()
    base_color = StringProperty('')
    curr_normal = ListProperty('')
    curr_down = ListProperty('')
    secondary_position_1 = ListProperty([])
    secondary_position_2 = ListProperty([])
    secondary_scale_1 = NumericProperty()
    secondary_scale_2 = NumericProperty()
    primary_position = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = None
        self.anim_scheduler = None

    def stop_effect_anims(self):
        """
        Stops the special effect animation of the button. This involves cancelling any
        ongoing animation and / or unscheduling scheduled animations that have been set
        by the reschedule method.
        """
        Animation.cancel_all(self)
        if self.anim_scheduler:
            self.anim_scheduler.cancel()
        self.reset_pos()

    def effect_anim(self, anim=None, widget=None):
        """
        Starts the special effect animation of the TriviaButton.
        Note that if the size changes during gameplay, for instance because the player
        alters the window size, the animation will be slightly off. Yet, this is not so important
        as the animation is stopped and restarted after every question (and hence the animation
        gets restarted using the correct self.width). So, the use of an on_width trigger is not
        really necessary.
        """
        self.anim = Animation(x_transform=self.width+20, duration=1)
        self.anim.bind(on_complete=self.reschedule)
        self.anim.start(self)

    def reschedule(self, anim=None, widget=None):
        """
        After the special animation has run once, this callback is called to reschedule
        it at a random time, so that there is a slight offset for the effect among the 
        TriviaButtons.
        A reference for the clock object is kept so that Animation can be cancelled, as
        Animation.cancel_all will only catch current animations, but not the scheduled ones.
        """
        self.reset_pos()
        self.anim_scheduler = Clock.schedule_once(self.reanim, randint(20, 40)/10)

    def reanim(self, dt=None):
        """Convenience function to swallow the dt argumemt of Clock callbacks."""
        self.anim.start(self)

    def reset_pos(self):
        """Resets the special effect animation to its initial settings."""
        self.x_transform = -20


class AnswerFeedbackLabel(Label):

    angle = NumericProperty()
    scale = NumericProperty()
    primary_angle = NumericProperty()
    primary_scale = NumericProperty()
    secondary_angle = NumericProperty()
    secondary_scale = NumericProperty()
    sentiment = StringProperty()

    def animate(self):
        anim_opacity = Animation(opacity=1, duration=0.5) + Animation(opacity=0, duration=0.5)
        anim_scale = Animation(scale=self.secondary_scale, angle=self.secondary_angle, duration=1)
        anim_full = anim_opacity & anim_scale
        anim_full.bind(on_complete=self.reset_pos)
        anim_full.start(self)

    def reset_pos(self, anim=None, widget=None):
        self.scale = self.primary_scale
        self.angle = self.primary_angle

class PressOK(Label):
    pass

class PressColor(BoxLayout):

    pre_text = StringProperty('')
    post_text = StringProperty('')
    butt_text = StringProperty('')
    butt_col = ListProperty([1,1,1,1])
    font_size = NumericProperty()

class QuestionLabel(Label):

    secondary_position_1 = ListProperty()
    secondary_position_2 = ListProperty()
    primary_position = ListProperty()
    parent_width = NumericProperty()
    mask_width = NumericProperty(0)
    bg_pos = ListProperty([0,0])
    bg_size = ListProperty([0,0])

    def anim_mask_open(self):
        """Widens the stencil mask so that the text becomes visible."""
        anim = Animation(mask_width=self.bg_size[0], t='out_quad', duration=1)
        anim.start(self)

    def reset_pos(self, anim=None, widget=None):
        self.mask_width = 0

class Round(BoxLayout):
    pass


class OptionButton(ButtonBehavior, FocusBehavior, Label):

    scale = NumericProperty()
    arrow_left = ListProperty()
    arrow_right = ListProperty()
    multiple_choice = BooleanProperty()
    show_arrow = BooleanProperty()
    action_target = ObjectProperty()
    choices = ListProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.focus_anim = Animation()
        self.opt_index = -1
        self.original_text = None

    def on_focus(self, widget=None, focus=None):
        self.focus_anim.cancel(self)
        if self.focus:
            print("Focus!")
            print("Current value: {}".format(getattr(App.get_running_app(), self.action_target) if self.action_target else 'N/A'))
            self.set_rand_outline()
            self.focus_anim = Animation(scale=1.15, duration=0.3, t='out_elastic')
            self.focus_anim.start(self)
            self.parent.current_focus = self
            App.get_running_app().snd_machine.btn_sel()
        else:
            self.close_choices()
            self.focus_anim = Animation(scale=1., duration=0.3, t='out_elastic')
            self.focus_anim.start(self)
    
    def set_rand_outline(self):
        self.outline_color = [randint(0,9)/10 for x in range(3)]

    def on_press(self, *args, **kwargs):
        super().on_press(*args, **kwargs)
        if self.multiple_choice and not self.show_arrow:
            self.show_arrow = True
            curr_option_value = getattr(App.get_running_app(), self.action_target)
            if self.opt_index < 0:
                self.original_text = self.text
                self.opt_index = 0
                for index, choice in enumerate(self.choices):
                    if choice[1] == curr_option_value:
                        self.opt_index = index
                        break
            self.text = self.choices[self.opt_index][0]
            App.get_running_app().snd_machine.btn_mov()
        elif self.multiple_choice and self.show_arrow:
            self.show_arrow = False
            self.close_choices()
            App.get_running_app().snd_machine.btn_sel()

    def close_choices(self):
        if self.opt_index > -1:
            self.opt_index = -1
            self.text = self.original_text

    def option_prev(self):
        if self.show_arrow:
            App.get_running_app().snd_machine.btn_mov()
            if self.opt_index > 0:
                self.opt_index -= 1
            self.text = self.choices[self.opt_index][0]
            self.option_set()

    def option_next(self):
        if self.show_arrow:
            App.get_running_app().snd_machine.btn_mov()
            if self.opt_index < len(self.choices)-1:
                self.opt_index += 1
            self.text = self.choices[self.opt_index][0]
            self.option_set()

    def option_set(self):
        setattr(App.get_running_app(), self.action_target, self.choices[self.opt_index][1])

class OptionIndicator(Widget):
    
    x_transform = NumericProperty()
    x_transform_max = NumericProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.anim = None
        
    def on_y(self, *args):
        print("ON Y: {}, args: {}".format(self.y, args))
        
    def on_x_transform_max(self, widget, transform_value):
        Animation.cancel_all(self)
        self.anim = Animation(x_transform=self.x_transform_max, t='in_cubic',duration=0.5)+Animation(x_transform=0, t='out_cubic', duration=0.5)
        self.anim.repeat = True
        self.anim.start(self)


class Difficulty(BoxLayout):
   
   indicator_layout_pos = ListProperty()
   indicator_layout = ObjectProperty(rebind=True)

class Difficulty_Indicator(Widget):

    scale = NumericProperty()
    indicator_size = ListProperty()
    indicator_color = ListProperty()
    widget_difficulty = StringProperty()
    current_difficulty = StringProperty()
    visible = BooleanProperty()
    fore_opacity = NumericProperty()

class GameInfo(BoxLayout):

    secondary_position = ListProperty()
    primary_position = ListProperty()
    
class ScrollLabel(ScrollView):

    label_text = StringProperty()
    font_size = NumericProperty()
    font_name = StringProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next_label_text = None
        self.scroll_anim = None
        self.scroll_anim_scheduler = None

    def on_label_text(self, widget, label_text):
        """
        The label to be displayed has changed, this means we want to animate out the currently
        scrolling label and fade back in the label with the new text.
        We first save the new label text in a variable and start the fade out animation.
        """
        #self.next_label_text = label_text
        self.fade_out_animation()

    def fade_out_animation(self):
        """
        Starts the fade out animation, but only if opacity is not already 0 (might happen if
        this is the first time the label receives a text for example).
        """
        if self.opacity == 0:
            self.fade_in_animation()
        else:
            anim_out = Animation(opacity=0, duration=0.2)
            anim_out.bind(on_complete=self.fade_in_prep)
            anim_out.start(self)

    def fade_in_prep(self, anim=None, widget=None):
        """
        This function gets called at the end of the fade out animation and prepares the
        fade in animation, for example by actually setting the label's text to the desired value
        and resetting positions etc.
        At the end, we schedule the fade in for the next frame. We do it this way so the label's
        properties are updated correctly (as we need its width).
        """
        self.ids.scrollable_label.text = self.label_text
        Animation.cancel_all(self)
        self.reset_pos()
        Clock.schedule_once(self.fade_in_animation)

    def fade_in_animation(self, dt=None):
        """
        Starts the fade in animation.
        """
        self.scroll_anim = Animation(scroll_x=1, duration=(self.ids.scrollable_label.width / 300))
        self.scroll_anim.bind(on_complete=self.scroll_reschedule)
        self.scroll_anim.start(self)
        Animation(opacity=1, duration=0.2).start(self)
        
    def scroll_reschedule(self, anim=None, widget=None):
        """
        Gets called at the end of each scroll animation and basically resets and reschedules it for the next frame.
        """
        self.reset_pos()
        self.scroll_anim_scheduler = Clock.schedule_once(self.scroll_reanim)

    def scroll_reanim(self, dt=None):
        """
        Convenience function to restart the scroll animation.
        """
        self.scroll_anim.start(self)

    def reset_pos(self, *args):
        """
        Resets some values to initial state.
        """
        self.scroll_x = 0


class Category(BoxLayout):

    cat = ObjectProperty(rebind=True)
    scroll_size = ListProperty()
    spacer_width = NumericProperty()

class ScrollSelector(Widget):
    pass

class Feduquiz(App):
    title = 'Feduquiz'

    bg_col = ListProperty([0, 0, 0])

    trivia = Trivia(USE_SAMPLE_DATA)

    curr_question = StringProperty()
    curr_type = StringProperty()
    curr_difficulty = StringProperty()
    curr_category = StringProperty()
    curr_correct = StringProperty()
    curr_wrong = ListProperty([])
    curr_btn_labels = ListProperty([])
    curr_score = NumericProperty(0)
    curr_round = NumericProperty(0)
    curr_total_rounds = NumericProperty(0)
    curr_verdict = StringProperty()

    opt_difficulty = StringProperty('')
    opt_category = NumericProperty(0)
    opt_amount = NumericProperty(10)
    opt_instant_fb = BooleanProperty(True)
    opt_type = StringProperty('')

    categories = ListProperty([['All', 0]])
    
    instruction_text = StringProperty(INSTRUCTION_TEXT)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.categories = get_categories()
        self.fps_event = Clock.schedule_interval(self.print_fps, 1/2.0)
        self.sm = None
        self.bg_anim = (Animation(bg_col=[1,0,0], duration=2) +
                Animation(bg_col=[1,1,0], duration=2) +
                Animation(bg_col=[0, 1, 1], duration=2) +
                Animation(bg_col=[0, 0, 1], duration=2) +
                Animation(bg_col=[1, 0, 1], duration=2))
        self.bg_anim.repeat = True

        self.snd_machine = SoundMachine()
        #self.bg_anim.start(self)   # Will be started by first screen (Intro)

        self.callbacks = []

        # Register EXIT and SCREENSHOT handler
        self.add_callback(CEC_CMD_MAP["EXIT"], "ALL", lambda: App.get_running_app().stop())

        # Set window size if instructed
        if SET_SIZE:
            Window.size = (1920, 1080)
            Window.left = 0
            Window.top = 1

        # Get keyboard
        #self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        Window.bind(on_key_down=self._on_keyboard_down)

        # initialise libCEC
        if not DISABLE_CEC:
            from cec_control import pyCecClient
            self.lib = pyCecClient()
            self.lib.SetCommandCallback(lambda cmd: self.command_callback(cmd, 'cec'))

            # initialise libCEC and enter the main loop
            self.lib.InitLibCec()

    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(Intro(name='intro'))
        self.sm.add_widget(Game(name='game'))
        self.sm.add_widget(Score(name='score'))
        self.sm.add_widget(Options(name='options'))
        self.sm.add_widget(Instructions(name='instructions'))
        self.sm.add_widget(Credits(name='credits'))
        return self.sm

    def load_game(self, anim=None, widget=None):
        self.trivia.new_game(self.opt_difficulty, self.opt_category, self.opt_amount, self.opt_type)
        Clock.schedule_once(self.check_switch_screen)

    def check_switch_screen(self, dt=None):
        if not self.trivia.running:
            Clock.schedule_once(self.check_switch_screen)
            return
        self.sm.current = 'game'
        self.snd_machine.mode_game()

    def goto_screen(self, dt=None, s_name=None):
        if s_name:
            self.sm.current = s_name
            self.snd_machine.mode_menu()

    @mainthread
    def command_callback(self, cmd, origin):
        """Callback function for the CEC module"""
        print("{} command received: {}".format(origin, cmd))
        current = self.sm.current
        match = False
        for callback in self.callbacks:
            if cmd in callback[0] and (callback[1] == "ALL" or current == callback[1]):
                callback[2]()
                match = True
                print("Callback executed")
        return match


    def add_callback(self, cmd, screen, callback):
        """Adds a callback within the app."""
        print("Adding callback " + str(callback) + " for screen " + screen + " for command " + str(cmd))
        self.callbacks.append([cmd, screen, callback])


    def _on_keyboard_down(self, window, keycode, scancode, text, modifiers, **kwargs):
        print('The key {} {} {} has been pressed'.format(keycode, 'with text '+text if text else '', 'and modifiers '+str(modifiers) if len(modifiers)>0 else ''))

        # Call callback
        return self.command_callback(keycode, 'keyboard')

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        #return True
        
    def print_fps(self, *args):
        fps = Clock.get_fps()
        print("{} Fps    ".format(int(fps)), end='\r')

if __name__ == '__main__':
    Feduquiz().run()