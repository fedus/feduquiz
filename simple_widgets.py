#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.uix.label import Label
from kivy.uix.effectwidget import EffectWidget
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.graphics.opengl import *
from kivy.graphics import *
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock

from random import randrange

class MainTitle(Label):

    scale = NumericProperty(1)

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

class RoundedBox(BoxLayout):
    pass

class PlayOrOptions(RoundedBox):
    pass

class PressOK(Label):
    pass

class PressColor(BoxLayout):

    pre_text = StringProperty('')
    post_text = StringProperty('')
    butt_text = StringProperty('')
    butt_col = ListProperty([1,1,1,1])
    font_size = NumericProperty()

class LoadingSpinner(Widget):

    inner_ellipse_size: NumericProperty()
    angle_start: NumericProperty(0)
    angle_end: NumericProperty(0)
    random_rotation: NumericProperty(0)
    
    def __init__(self, *args, **kwargs):
        super(LoadingSpinner, self).__init__(*args, **kwargs)
        self.anim = (
            Animation(angle_end=360, t='in_out_quint', duration=0.75)
            + Animation(angle_start=360, t='in_out_quint', duration=0.75)
            + Animation(angle_end=0, angle_start=0, duration=0)
        )
        self.anim.bind(on_complete=lambda widget, animation: self.reset_and_generate_new_random_rotation())
        Clock.schedule_once(lambda dt: self.anim.start(self))

    def reset_and_generate_new_random_rotation(self):
        self.random_rotation = randrange(0, 361, 1)
        Clock.schedule_once(lambda dt: self.anim.start(self))

class LoadingNotice(BoxLayout):
    pass