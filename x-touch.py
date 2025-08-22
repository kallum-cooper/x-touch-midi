#!/usr/bin/env python3
import rtmidi
import subprocess
import re

# === CONFIGURATION ===
# Map each knob/slider to the application you want to control
knob_apps = {
    1: "Google Chrome",
    2: "Google Chrome",
    3: "Chrome",
    4: "VLC",
    5: "Spotify",
    6: "Firefox",
    7: "Discord",
    # knob 8 will be the focused window
}

MIDI_DEVICE_NAME = "X-TOUCH MINI MIDI 1"  # exact name from `aconnect -l`

# === HELPER FUNCTIONS ===
def set_app_volume(app_name, value):
    """Set the volume of a specific application (0-127 MIDI -> 0-100%)."""
    volume_percent = int((value / 127) * 100)

    # get the sink-input list
    result = subprocess.run(
        ["pactl", "list", "sink-inputs"], capture_output=True, text=True
    )

    sink_index = None
    lines = result.stdout.splitlines()
    for i, line in enumerate(lines):
        if app_name.lower() in line.lower():
            # look backwards for "Sink Input #" line
            for j in range(i, -1, -1):
                if "Sink Input" in lines[j]:
                    sink_index = lines[j].split("#")[1].strip()
                    break
            if sink_index:
                break

    if sink_index:
        subprocess.run(
            ["pactl", "set-sink-input-volume", sink_index, f"{volume_percent}%"]
        )
        print(f"{app_name} volume set to {volume_percent}%")
    else:
        print(f"Application '{app_name}' not found.")


def set_focused_window_volume(value):
    """Set volume for the focused window using process name matching."""
    try:
        pid = subprocess.check_output(
            ["xdotool", "getwindowfocus", "getwindowpid"],
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("No focused window detected.")
        return

    try:
        proc_name = subprocess.check_output(
            ["ps", "-p", pid, "-o", "comm="], text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("Could not get process name for focused window.")
        return

    result = subprocess.run(
        ["pactl", "list", "sink-inputs"], capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    sink_index = None
    for i, line in enumerate(lines):
        # match the process name in the sink info
        if re.search(proc_name, line, re.IGNORECASE):
            for j in range(i, -1, -1):
                if "Sink Input" in lines[j]:
                    sink_index = lines[j].split("#")[1].strip()
                    break
            if sink_index:
                break

    if sink_index:
        volume_percent = int((value / 127) * 100)
        subprocess.run(
            ["pactl", "set-sink-input-volume", sink_index, f"{volume_percent}%"]
        )
        print(f"Focused window ({proc_name}) volume set to {volume_percent}%")
    else:
        print(f"Could not find sink for process '{proc_name}'")


# === MIDI SETUP ===
midi_in = rtmidi.MidiIn()
available_ports = midi_in.get_ports()
print("Available input ports:", available_ports)

# find the correct port
port_index = None
for i, port_name in enumerate(available_ports):
    if MIDI_DEVICE_NAME in port_name:
        port_index = i
        break

if port_index is None:
    print(f"Error: MIDI device '{MIDI_DEVICE_NAME}' not found.")
    exit(1)

midi_in.open_port(port_index)
print(f"Listening to {MIDI_DEVICE_NAME}...")

# === MAIN LOOP ===
try:
    while True:
        msg = midi_in.get_message()
        if msg:
            message, delta = msg
            # MIDI CC messages: [status, control, value]
            if message[0] & 0xF0 == 0xB0:  # Control Change
                control = message[1] + 1  # CC numbers start at 0
                value = message[2]
                if control in knob_apps:
                    set_app_volume(knob_apps[control], value)
                elif control == 8:
                    set_focused_window_volume(value)

except KeyboardInterrupt:
    print("Exiting...")
finally:
    midi_in.close_port()

