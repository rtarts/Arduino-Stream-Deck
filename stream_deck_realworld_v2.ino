// ============================================================
//  DIY Stream Deck — Real world version (7 buttons)
//  D2–D7 = 6 macro buttons (left to right)
//  D8    = layer switch
//  D11   = LED layer indicator
//  A4    = OLED SDA
//  A5    = OLED SCL
//
//  OLED layout:
//    ┌────────────────────────────┐
//    │ Layer: General             │  ← header bar (inverted)
//    ├────┬────┬────┬────┬────┬──┤
//    │ B1 │ B2 │ B3 │ B4 │ B5 │B6│  ← label strip
//    └────┴────┴────┴────┴────┴──┘
//
//  Libraries needed:
//    - Adafruit SSD1306
//    - Adafruit GFX Library
// ============================================================

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// ── OLED ─────────────────────────────────────────────────────
#define SCREEN_WIDTH  128
#define SCREEN_HEIGHT  64
#define OLED_RESET     -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// ── Pins ─────────────────────────────────────────────────────
const int BTN_PINS[7] = {2, 3, 4, 5, 6, 7, 8};
const int LED_PIN      = 11;

// ── Layers ───────────────────────────────────────────────────
#define NUM_LAYERS 2
int currentLayer = 0;

const char* layerNames[NUM_LAYERS] = {
  "Layer 1",
  "Layer 2"
};

// Labels for each button per layer — max 4 chars to fit strip
// Index 0–5 = B1–B6 (D2–D7). D8 is always layer switch.
const char* labels[NUM_LAYERS][6] = {
  {"Copy", "Pste", "Undo", "Save", "NTab", "CTab"},  // General
  {"Inv",  "Cvr",  "Snk",  "Veh",  "Chat", "Entr"}  // Gaming
};

// ── Debounce ─────────────────────────────────────────────────
bool lastState[7];
unsigned long lastDebounce[7];
const unsigned long DEBOUNCE_MS = 50;

// ── LED blink ────────────────────────────────────────────────
void blinkLED(int times) {
  for (int i = 0; i < times; i++) {
    digitalWrite(LED_PIN, HIGH); delay(80);
    digitalWrite(LED_PIN, LOW);  delay(80);
  }
}

// ── OLED update ──────────────────────────────────────────────
// Layout: 128px wide, 64px tall
// Header: full width, 14px tall, inverted colours
// Strip:  6 cells across remaining 50px height
//         each cell = 128/6 = ~21px wide
void updateDisplay(int highlightBtn = -1) {
  display.clearDisplay();

  // ── Header bar ──
  display.fillRect(0, 0, SCREEN_WIDTH, 11, WHITE);
  display.setTextColor(BLACK);
  display.setTextSize(1);  // size 1 = 6x8px per char, smallest readable
  display.setCursor(3, 2);
  display.print(layerNames[currentLayer]);

  // ── Button label strip ──
  display.setTextColor(WHITE);
  int cellW = SCREEN_WIDTH / 6;  // 21px per cell

  for (int i = 0; i < 6; i++) {
    int x = i * cellW;
    int y = 12;
    int h = SCREEN_HEIGHT - 12;  // 52px tall — more room now

    // Divider line between cells
    if (i > 0) {
      display.drawLine(x, y, x, SCREEN_HEIGHT - 1, WHITE);
    }

    // Highlight active button with filled cell
    if (i == highlightBtn) {
      display.fillRect(x + 1, y, cellW - 1, h, WHITE);
      display.setTextColor(BLACK);
    } else {
      display.setTextColor(WHITE);
    }

    // Button number (small, top of cell)
    display.setTextSize(1);
    display.setCursor(x + 3, y + 3);
    display.print("B");
    display.print(i + 1);

    // Label (below number)
    display.setCursor(x + 2, y + 16);
    display.print(labels[currentLayer][i]);

    // Reset text colour after highlight
    display.setTextColor(WHITE);
  }

  // Outer border
  display.drawRect(0, 12, SCREEN_WIDTH, SCREEN_HEIGHT - 12, WHITE);

  display.display();
}

// ── Setup ────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  for (int i = 0; i < 7; i++) {
    pinMode(BTN_PINS[i], INPUT_PULLUP);
    lastState[i]    = HIGH;
    lastDebounce[i] = 0;
  }

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  if (!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    // OLED not found — rapid blink
    while (true) {
      digitalWrite(LED_PIN, !digitalRead(LED_PIN));
      delay(150);
    }
  }

  blinkLED(1);
  updateDisplay();

  Serial.println("READY");
  Serial.print("LAYER:"); Serial.println(currentLayer);
  Serial.print("LAYER_NAME:"); Serial.println(layerNames[currentLayer]);
}

// ── Loop ─────────────────────────────────────────────────────
void loop() {
  for (int i = 0; i < 7; i++) {
    bool state = digitalRead(BTN_PINS[i]);

    if (state == LOW && lastState[i] == HIGH) {
      unsigned long now = millis();
      if (now - lastDebounce[i] > DEBOUNCE_MS) {
        lastDebounce[i] = now;

        if (i == 6) {
          // D8 = layer switch
          currentLayer = (currentLayer + 1) % NUM_LAYERS;
          blinkLED(currentLayer + 1);
          updateDisplay();
          Serial.print("LAYER:"); Serial.println(currentLayer);
          Serial.print("LAYER_NAME:"); Serial.println(layerNames[currentLayer]);
        } else {
          // Flash the pressed button on OLED briefly
          updateDisplay(i);
          delay(120);
          updateDisplay();

          Serial.print("BTN:");
          Serial.print(currentLayer);
          Serial.print(":");
          Serial.println(i);
        }
      }
    }

    lastState[i] = state;
  }
}
