

# X-Touch MIDI Volume Controller

Control the volume of specific applications and the currently focused window using an X-Touch MINI MIDI controller on Linux (PulseAudio).

Knobs can be mapped to specific apps, and one knob can dynamically control the focused window's volume.


## Features
Map any knob to a specific application (e.g., Chrome, VLC, Spotify, Discord).

- Dedicated knob for controlling the focused window’s audio.
- Works with PulseAudio via pactl.
- Auto-start support via .desktop file (runs in background on login).
## Install dependencies:



```
sudo apt update
sudo apt install python3 python3-rtmidi xdotool pulseaudio-utils

```


## Installation

Clone the repo

```
git clone https://github.com/kallum-cooper/x-touch-midi.git
cd x-touch-midi
```
Edit config inside Py script

Open x-touch.py and adjust the mapping:

```
knob_apps = {
    1: "Google Chrome",
    2: "VLC",
    3: "Spotify",
    4: "Discord",
    # knob 8 controls the focused window
}

MIDI_DEVICE_NAME = "X-TOUCH MINI MIDI 1"  # check with `aconnect -l`

```

Run Manually

```
python3 x-touch.py
```

You should see and should repond to your outputs:

```
Available input ports: ['X-TOUCH MINI MIDI 1']
Listening to X-TOUCH MINI MIDI 1...
```

Autostart on login

Create a .desktop file in your autostart directory:
```
mkdir -p ~/.config/autostart
nano ~/.config/autostart/xtouch.desktop
```
Paste and change path:
```
[Desktop Entry]
Type=Application
Exec=/usr/bin/python3 /home/YOURUSER/x-touch-midi/x-touch.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=X-Touch Volume Control
```

Save + relog → it will start in the background.

