#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kivy.logger import Logger
from kivy.clock import Clock
from kivy.core.audio import SoundLoader

class SoundMachine:
    """Holds and plays sounds."""

    def __init__(self):
        """Initialise SoundLoaders."""
        self.snd_btn_sel = SoundLoader.load('resources/sfx_menu_select1.wav')
        self.snd_btn_mov = SoundLoader.load('resources/sfx_menu_move4.wav')
        self.snd_game = SoundLoader.load('resources/fast_level.wav')
        self.snd_menu = SoundLoader.load('resources/elevator.ogg')

    def btn_sel(self):
        """Sound to play for an OptionButton selection."""
        self.proxy(self.snd_btn_sel, "play")

    def btn_mov(self):
        """Sound to play for an OptionButton movement."""
        self.proxy(self.snd_btn_mov, "play")

    def mode_menu(self):
        """Switch background music to menu mode."""
        print("Playing menu theme")
        if self.proxy(self.snd_game, "state") == "play":
            self.proxy(self.snd_game, "stop")
        self.proxy(self.snd_menu, "loop", True)
        self.proxy(self.snd_menu, "play")

    def mode_game(self):
        """Switch background music to game mode."""
        print("Playing game theme")
        if self.proxy(self.snd_menu, "state") == "play":
            self.proxy(self.snd_menu, "stop")
        self.proxy(self.snd_game, "loop", True)
        Clock.schedule_once(lambda dt: self.proxy(self.snd_game, "play"), 0.25)
    
    def proxy(self, sound, command, new_val=None):
        """
        Various factors can have an impact on the ability to play a given sound
        format on a given machine. This command acts as a proxy for sound objects
        so that a warning can be printed to the console if something fails instead
        of raising an exception and quitting the game.
        """
        try:
            if new_val:
                return setattr(sound, command, new_val)
            else:
                temp_proxy = getattr(sound, command)
                if callable(temp_proxy):
                    return temp_proxy()
                else:
                    return temp_proxy
        except Exception as exc:
            Logger.exception("Could not proxy {} for sound {}{}. Exception: {}".format(command, sound, " with value {}".format(new_val) if new_val else "", exc))
