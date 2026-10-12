# DIY Arduino Stream Deck

A programmable 7-button macro pad built on an Arduino Uno. Six buttons trigger keyboard macros, a seventh switches between two **layers** (general shortcuts and gaming), and a 128x64 OLED shows the active layer and a label for each button. A Python script on the PC listens over serial and turns button presses into real keystrokes.

## Features

- 6 macro buttons plus a dedicated layer-switch button
- 2 layers (easy to extend in code)
- OLED header with layer name and a label strip for B1-B6; the pressed button flashes
- LED indicator that blinks once for Layer 1 and twice for Layer 2
- Software debounce (50 ms) on all buttons
- Python companion with logging and automatic Arduino port detection if the configured port fails

## How it works

```
Arduino Uno                              PC (Python)
-----------                              -----------
buttons (INPUT_PULLUP, debounced)        reads serial lines
OLED shows layer + labels     --USB-->   maps (layer, button) -> macro
sends BTN:<layer>:<index>                pynput sends the keystrokes
sends LAYER:<n>
```

**Serial protocol** (9600 baud): `READY`, `LAYER:<n>`, `LAYER_NAME:<name>`, `BTN:<layer>:<index>`.

## Default macros

| Button | Pin | Layer 1 (General) | Layer 2 (Gaming, GTA Online defaults) |
|--------|-----|-------------------|---------------------------------------|
| B1 | D2 | Copy (`Ctrl+C`) | Inventory menu (`M`) |
| B2 | D3 | Paste (`Ctrl+V`) | Cover (`Q`) |
| B3 | D4 | Undo (`Ctrl+Z`) | Sneak (`Caps Lock`) |
| B4 | D5 | Save (`Ctrl+S`) | Personal vehicle (`F6`) |
| B5 | D6 | New tab (`Ctrl+T`) | Text chat (`T`) |
| B6 | D7 | Close tab (`Ctrl+W`) | Enter |
| Layer switch | D8 | Toggles between layers | Toggles between layers |

## Hardware

| Part | Pin / connection |
|------|------------------|
| Arduino Uno | USB to PC |
| 6 macro buttons | D2-D7, other leg to GND (`INPUT_PULLUP`) |
| Layer switch button | D8, other leg to GND |
| Layer LED | D11 (use a series resistor) |
| SSD1306 128x64 OLED (I2C) | SDA = A4, SCL = A5, address `0x3C` |

## Software requirements

**Arduino (Library Manager):** Adafruit GFX Library, Adafruit SSD1306

**PC (Python 3):**
```bash
pip install pyserial pynput
```

## Setup

1. Wire the buttons, LED and OLED as shown above.
2. Open `stream_deck_realworld_v2.ino` in the Arduino IDE and upload it to the Uno.
3. Find the Arduino's COM port: **Device Manager > Ports (COM & LPT)**.
4. In `stream_deck.py`, set `COM_PORT` (for example `COM_PORT = "COM6"`).
5. Run the companion script:
   ```bash
   python stream_deck.py
   ```
6. Press a button. The OLED flashes it and the PC performs the macro.

Press `Ctrl+C` to stop. Events are logged to `stream_deck.log` (set `LOG_FILE = None` to disable).

**Run at Windows startup (no terminal window):** create a shortcut to `pythonw stream_deck.py` and place it in `shell:startup`.

## Customizing macros

Macros live in two places that need to stay in sync:

1. **`stream_deck.py`**: edit the `MACROS` dictionary. Keys are `(layer, button_index)`, and values are a label plus an action:
   ```python
   (0, 0): ("Copy", lambda: send(Key.ctrl, 'c')),   # key combo
   (1, 3): ("Personal veh", lambda: tap(Key.f6)),   # single key
   ```
   `send()` presses keys together; `tap()` presses and releases one key.
2. **`stream_deck_realworld_v2.ino`**: update the `labels` array (max 4 characters per label) so the OLED matches.

To add a layer, increase `NUM_LAYERS` and extend `layerNames` and `labels` in the sketch, then add matching entries to `MACROS` and `LAYER_NAMES` in the script.

## Troubleshooting

- **Could not open COM port:** wrong `COM_PORT`, or another program (such as the Serial Monitor) is using it. The script will try to auto-detect an Arduino, CH340 or CH341 device.
- **LED blinks rapidly at startup:** the OLED wasn't found. Check wiring and the I2C address.
- **Buttons do nothing on the PC:** make sure the baud rate is `9600` in both files and the script is running.
- **Macros fire in the wrong app:** keystrokes go to whichever window has focus.

## Files

| File | Purpose |
|------|---------|
| `stream_deck_realworld_v2.ino` | Arduino sketch: buttons, layers, OLED, LED, serial output |
| `stream_deck.py` | PC companion: reads serial events and sends keystrokes |
