from kivy.animation import Animation
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty, ListProperty, ObjectProperty

from enum import Enum

from constants import TIMER_WARNING

class TimerStates(Enum):
    RUNNING = 1
    WARN = 2
    LAPSED = 3
    STOPPED = 4

class Timer(EventDispatcher):

    current_percentage = NumericProperty(0)
    current_state = ObjectProperty(TimerStates.STOPPED)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.running = False
        self.seconds = 0
        self.callback = None
        self.resetting = False
        self.timer_animation = Animation()

    def on_current_percentage(self, widget, new_percentage):
        if not self.running:
            self.current_state = TimerStates.STOPPED
        elif self.resetting or new_percentage > TIMER_WARNING:
            self.current_state = TimerStates.RUNNING
        elif 0 < new_percentage <= TIMER_WARNING:
            self.current_state = TimerStates.WARN
        else:
            self.current_state = TimerStates.LAPSED

    def start_timer(self, seconds, callback=None, windup=True, reset=True):
        """
        (Re)starts the timer
        """
        print('Starting timer ...')
        self.running = True
        self.resetting = True
        if reset:
            self.reset_timer()
        self.callback = callback
        self.seconds = seconds
        self.timer_animation.cancel(self)
        duration = 0.5 if windup else 0
        self.timer_animation = Animation(current_percentage=1, duration=duration)
        self.timer_animation.bind(on_complete=self.run_timer)
        self.timer_animation.start(self)

    def run_timer(self, anim=None, widget=None):
        self.resetting = False
        self.timer_animation = Animation(current_percentage=0, duration=self.seconds)
        self.timer_animation.bind(on_complete=self.reset_running)
        self.timer_animation.start(self)

    def halt_timer(self):
        if self.current_state is not TimerStates.LAPSED:
            self.timer_animation.cancel(self)
            self.current_state = TimerStates.STOPPED

    def reset_running(self, anim=None, widget=None):
        self.running = False
        self.current_state = TimerStates.LAPSED
        if self.callback:
            self.callback()

    def reset_timer(self):
        self.timer_animation.cancel(self)
        self.current_percentage = 0