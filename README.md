# Feduquiz

This is a trivia app built with Kivy, and is supposed to be played on a television. It is then controlled with the
television's own remote control.

On a Raspberry Pi, no special setup should be necessary, and HDMI-CEC signals are captured using the included
cec_control.py ((c) by PulseEight) file. On other systems, it might be necessary to install adequate libraries or
third party tools. For instance, on an Udoo X86, the CEC kernel module provided by Udoo can be compiled and
loaded. Only the keytable needs to be adapted in that case.

Finally, the game can also be played on any normal device using a standard keyboard. The letters R, B, Y and G can
be used to press the RED, BLUE, YELLOW and GREEN buttons respectively.

Some useful CLI options:

Argument | Explanation
------------ | -------------
--disable-cec | Don't load the PulseEight CEC library (use this if not using a Raspberry Pi)
--use-sample-data | Use static sample quiz data provided in the sample_quiz_data.json file, avoids unnecessary queries to OpenTDB
--set-size | Force the Kivy window to be sized to 1920x1080px (FullHD), which is the intended window size of the app
--delay-start | Wait for the user to click inside the window before launching the title screen animation

*This app is still under construction.*

## Screenshots

![Title screen](https://raw.githubusercontent.com/fedus/feduquiz/master/screenshots/01_title.png)
![Options screen](https://raw.githubusercontent.com/fedus/feduquiz/master/screenshots/02_options.png)
![Game screen](https://raw.githubusercontent.com/fedus/feduquiz/master/screenshots/03_game.png)
![Score screen](https://raw.githubusercontent.com/fedus/feduquiz/master/screenshots/04_score.png)

## Credits

### Fonts
BalooThambi: (c) EkType, https://github.com/EkType/Baloo<br>
Londrina: (c) Marcelo Magalhães, https://github.com/marcelommp/Londrina-Typeface/<br>
LuckiestGuy: (c) Astigmatic, https://fonts.google.com/specimen/Luckiest+Guy<br>
Press Start 2P: (c) Cody "CodeMan38" Boisclair, https://fonts.google.com/specimen/Press+Start+2P

### Sounds & music
Menu Sfx: (c) Juhani Junkala, https://juhanijunkala.com/<br>
Menu music - Somewhere in the elevator: (c) Peachtea, https://soundcloud.com/noah-cedeno-657159350<br>
Game music - Fast Level Loop 8 Bit Chiptune: (c) wyver9, https://wyver9.bandcamp.com/album/arcade-8-bit-loops-battletoads-style

### Questions
Trivia api: (c) Open Trivia Database, https://www.opentdb.com<br>