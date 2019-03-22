#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.properties import ListProperty, BooleanProperty, NumericProperty, ObjectProperty

from random import randint


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
            opacity = (((widget_xy[1] + widget.height) - self.y) / widget.height) if widget.height > 0 else 0
            return opacity
        elif widget_tr[1] > self.top:
            opacity = ((self.top - widget_xy[1]) / widget.height) if widget.height > 0 else 0
            return opacity
        return 1

    def on_scroll_y(self, *args):
        """
        Prompts the BoxLayout contained within the FreeScrollView to
        walk through its children and adapt their opacity.
        """
        # print("Scroll y  {}".format(str(args)))
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
        rel_pos = widget_pos_in_parent / self.height
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
            print("Current value: {}".format(
                getattr(App.get_running_app(), self.action_target) if self.action_target else 'N/A'))
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
        self.outline_color = [randint(0, 9) / 10 for x in range(3)]

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
            if self.opt_index < len(self.choices) - 1:
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
        self.anim = Animation(x_transform=self.x_transform_max, t='in_cubic', duration=0.5) + Animation(x_transform=0,
                                                                                                        t='out_cubic',
                                                                                                        duration=0.5)
        self.anim.repeat = True
        self.anim.start(self)