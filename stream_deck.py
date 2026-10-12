"""
DIY Stream Deck — Python Companion Script
7 buttons: D2–D7 = macros, D8 = layer switch
2 layers: Layer 1 (general), Layer 2 (gaming/media)

Requirements:
    pip install pyserial pynput

Usage:
    1. Flash stream_deck_realworld_v2.ino to your Uno
    2. Find your COM port in Device Manager → Ports
    3. Update COM_PORT below
    4. Run: python stream_deck.py
    5. Press Ctrl+C to stop

To add to Windows startup (no terminal window):
    - Create a shortcut to: pythonw stream_deck.py
    - Drop it in: shell:startup
"""

import serial
import serial.tools.list_ports
import time
import sys
import logging
from pynput.keyboard import Key, Controller

# ── Config ───────────────────────────────────────────────────
COM_PORT  = "COM6"   # ← update this to your Arduino's COM port
BAUD_RATE = 9600
LOG_FILE  = "stream_deck.log"  # set to None to disable

# ── Logging ──────────────────────────────────────────────────
handlers = [logging.StreamHandler(sys.stdout)]
if LOG_FILE:
    handlers.append(logging.FileHandler(LOG_FILE))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=handlers
)
log = logging.getLogger("stream_deck")

# ── Keyboard ─────────────────────────────────────────────────
keyboard = Controller()

def send(*keys):
    """Press a key combination then release all."""
    for k in keys:
        keyboard.press(k)
    time.sleep(0.05)
    for k in reversed(keys):
        keyboard.release(k)

def tap(key):
    keyboard.press(key)
    time.sleep(0.05)
    keyboard.release(key)

# ── Macros ───────────────────────────────────────────────────
# Layout:
#   (layer, button_index) : ("label", action)
#   layer 0 = Layer 1, layer 1 = Layer 2
#   button index 0–5 = B1–B6 (D2–D7)
#   D8 (index 6) is layer switch — handled by Arduino, not here
#
# To customise: change the lambda on any line.
# send() takes one or more keys pressed together.
# tap() presses and releases a single key.
# Key.ctrl, Key.alt, Key.shift, Key.f1 etc. from pynput.

MACROS = {
    # ── Layer 1 — General shortcuts ──────────────────────────
    (0, 0): ("Copy",         lambda: send(Key.ctrl, 'c')),
    (0, 1): ("Paste",        lambda: send(Key.ctrl, 'v')),
    (0, 2): ("Undo",         lambda: send(Key.ctrl, 'z')),
    (0, 3): ("Save",         lambda: send(Key.ctrl, 's')),
    (0, 4): ("New tab",      lambda: send(Key.ctrl, 't')),
    (0, 5): ("Close tab",    lambda: send(Key.ctrl, 'w')),

    # ── Layer 2 — Gaming (GTA Online defaults) ───────────────
    (1, 0): ("Inv menu",     lambda: tap('m')),
    (1, 1): ("Cover",        lambda: tap('q')),
    (1, 2): ("Sneak",        lambda: tap(Key.caps_lock)),
    (1, 3): ("Personal veh", lambda: tap(Key.f6)),
    (1, 4): ("Text chat",    lambda: tap('t')),
    (1, 5): ("Enter",        lambda: tap(Key.enter)),
}

LAYER_NAMES = {0: "Layer 1", 1: "Layer 2"}
current_layer = 0

# ── Serial connection ────────────────────────────────────────
def find_arduino():
    """Scan ports for an Arduino if the configured port fails."""
    for p in serial.tools.list_ports.comports():
        desc = p.description or ""
        if "Arduino" in desc or "CH340" in desc or "CH341" in desc:
            return p.device
    return None

def connect():
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        log.info(f"Connected on {COM_PORT}")
        return ser
    except serial.SerialException:
        log.warning(f"Could not open {COM_PORT} — scanning for Arduino...")
        detected = find_arduino()
        if detected:
            ser = serial.Serial(detected, BAUD_RATE, timeout=1)
            log.info(f"Found Arduino on {detected}")
            return ser
        log.error("No Arduino found. Check USB cable and COM port.")
        sys.exit(1)

# ── Message handler ──────────────────────────────────────────
def handle(line, layer):
    line = line.strip()
    if not line:
        return layer

    if line == "READY":
        log.info("Arduino ready")

    elif line.startswith("LAYER:"):
        try:
            layer = int(line.split(":")[1])
            log.info(f"── Switched to {LAYER_NAMES.get(layer, layer)}")
        except (IndexError, ValueError):
            log.warning(f"Bad LAYER message: {line}")

    elif line.startswith("BTN:"):
        try:
            parts     = line.split(":")
            btn_layer = int(parts[1])
            btn_idx   = int(parts[2])
            key       = (btn_layer, btn_idx)

            if key in MACROS:
                label, action = MACROS[key]
                log.info(f"B{btn_idx + 1} [{LAYER_NAMES.get(btn_layer, btn_layer)}] → {label}")
                action()
            else:
                log.warning(f"No macro assigned for {key}")
        except (ValueError, IndexError):
            log.warning(f"Bad BTN message: {line}")

    elif line.startswith("LAYER_NAME:"):
        log.info(f"Layer name: {line.split(':', 1)[1]}")

    else:
        log.debug(f"Unknown: {line}")

    return layer

# ── Main ─────────────────────────────────────────────────────
def main():
    log.info("Stream Deck started — Ctrl+C to stop")
    log.info(f"{len(MACROS)} macros loaded across {len(LAYER_NAMES)} layers")

    ser = connect()
    time.sleep(2)          # wait for Uno to reset after serial connect
    ser.reset_input_buffer()

    global current_layer

    try:
        while True:
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode("utf-8").strip()
                except UnicodeDecodeError:
                    continue
                current_layer = handle(line, current_layer)
            time.sleep(0.01)

    except KeyboardInterrupt:
        log.info("Stopped.")
    except serial.SerialException as e:
        log.error(f"Serial error: {e}")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
