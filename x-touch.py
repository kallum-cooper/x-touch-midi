#!/usr/bin/env python3
import rtmidi
import subprocess
import re
import tkinter as tk

# === CONFIGURATION ===
knob_apps = {
    1: "Chrome",
    2: "Google Chrome",
    3: "Chrome",
    4: "VLC",
    5: "Spotify",
    6: "Firefox",
    7: "Discord",
    # knob 8 -> focused window
}
MIDI_DEVICE_NAME = "X-TOUCH MINI MIDI 1"  # exact name from `aconnect -l`
OSD_HIDE_MS = 700                         # how long to show after last update


# === OSD (lightweight floating HUD) ===
class VolumeOSD:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        try:
            # helps avoid taskbar focus (may be ignored on some WMs)
            self.root.wm_attributes("-type", "dock")
        except tk.TclError:
            pass

        self.frame = tk.Frame(self.root, bg="#202225", bd=0, highlightthickness=0)
        self.frame.pack(fill="both", expand=True)

        self.label_var = tk.StringVar(value="")
        self.label = tk.Label(
            self.frame, textvariable=self.label_var,
            fg="#ffffff", bg="#202225", font=("Sans", 12, "bold")
        )
        self.label.pack(padx=14, pady=(10, 6), anchor="center")

        self.canvas = tk.Canvas(self.frame, width=260, height=12,
                                bg="#202225", highlightthickness=0, bd=0)
        self.canvas.pack(padx=14, pady=(0, 12))

        self._hide_after = None
        self._win_w, self._win_h = 320, 60

    def _position(self):
        # bottom center, slight offset up
        sw = self.root.winfo_screenwidth()
        x = sw - self._win_w - 30
        y = 30
        self.root.geometry(f"{self._win_w}x{self._win_h}+{x}+{y}")

    def show(self, label, percent):
        # update text
        self.label_var.set(f"{label}: {percent}%")

        # draw bar
        self.canvas.delete("all")
        w, h = 260, 12
        self.canvas.create_rectangle(0, 0, w, h, outline="#666", width=1)
        fill_w = max(1, int(w * (percent / 100.0)))
        self.canvas.create_rectangle(1, 1, fill_w, h - 1, outline="", fill="#48c774")

        # show window
        self._position()
        self.root.deiconify()
        if self._hide_after:
            self.root.after_cancel(self._hide_after)
        self._hide_after = self.root.after(OSD_HIDE_MS, self.root.withdraw)


# === AUDIO HELPERS ===
def set_app_volume(app_name, value, osd):
    """Set the volume of a specific app (0–127 MIDI -> 0–100%)."""
    volume_percent = int((value / 127) * 100)

    result = subprocess.run(
        ["pactl", "list", "sink-inputs"], capture_output=True, text=True
    )

    sink_index = None
    lines = result.stdout.splitlines()
    for i, line in enumerate(lines):
        if app_name.lower() in line.lower():
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
        osd.show(app_name, volume_percent)
    else:
        # optional: still show HUD so you see it tried
        osd.show(f"{app_name} (not found)", volume_percent)


def set_focused_window_volume(value, osd):
    """Set volume for the focused window by matching its process in sink-inputs."""
    try:
        pid = subprocess.check_output(
            ["xdotool", "getwindowfocus", "getwindowpid"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return

    try:
        proc_name = subprocess.check_output(
            ["ps", "-p", pid, "-o", "comm="], text=True
        ).strip()
    except subprocess.CalledProcessError:
        return

    result = subprocess.run(
        ["pactl", "list", "sink-inputs"], capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    sink_index = None
    for i, line in enumerate(lines):
        if re.search(proc_name, line, re.IGNORECASE):
            for j in range(i, -1, -1):
                if "Sink Input" in lines[j]:
                    sink_index = lines[j].split("#")[1].strip()
                    break
            if sink_index:
                break

    volume_percent = int((value / 127) * 100)
    if sink_index:
        subprocess.run(
            ["pactl", "set-sink-input-volume", sink_index, f"{volume_percent}%"]
        )
        osd.show(proc_name, volume_percent)
    else:
        osd.show(f"{proc_name} (no sink)", volume_percent)


# === MIDI + MAIN LOOP (poll via Tk .after) ===
def main():
    osd = VolumeOSD()

    midi_in = rtmidi.MidiIn()
    ports = midi_in.get_ports()
    print("Available input ports:", ports)

    port_index = None
    for i, name in enumerate(ports):
        if MIDI_DEVICE_NAME in name:
            port_index = i
            break
    if port_index is None:
        print(f"Error: MIDI device '{MIDI_DEVICE_NAME}' not found.")
        return

    midi_in.open_port(port_index)
    print(f"Listening to {MIDI_DEVICE_NAME}...")

    def poll_midi():
        # drain all pending messages each tick
        while True:
            msg = midi_in.get_message()
            if not msg:
                break
            message, _delta = msg
            if message[0] & 0xF0 == 0xB0:  # Control Change
                control = message[1] + 1    # CC numbers start at 0
                value = message[2]
                if control in knob_apps:
                    set_app_volume(knob_apps[control], value, osd)
                elif control == 8:
                    set_focused_window_volume(value, osd)
        osd.root.after(5, poll_midi)  # ~200Hz polling; adjust if needed

    osd.root.after(5, poll_midi)
    try:
        osd.root.mainloop()
    finally:
        midi_in.close_port()


if __name__ == "__main__":
    main()