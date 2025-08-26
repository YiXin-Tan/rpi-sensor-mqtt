#!/usr/bin/env python3
import os
import time
import signal
import sys
from dotenv import load_dotenv

from gpiozero import Button, RotaryEncoder, Device
from gpiozero.pins.pigpio import PiGPIOFactory

import paho.mqtt.client as mqtt

# ---- Config ----
load_dotenv()
MQTT_HOST = os.getenv("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USER", "")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "inputs/rotary/lamp")   # single topic
STEP_PCT = int(os.getenv("STEP_PCT", "5"))                   # HA brightness_step_pct per tick
DEBOUNCE_MS = int(os.getenv("DEBOUNCE_MS", "2"))             # small filter for chatter

GPIO_CLK = int(os.getenv("GPIO_CLK", "17"))
GPIO_DT = int(os.getenv("GPIO_DT", "18"))
GPIO_SW = int(os.getenv("GPIO_SW", "27"))

# Use pigpio for robust edge handling
Device.pin_factory = PiGPIOFactory()

# ---- MQTT ----
client = mqtt.Client(client_id="rpi-sensor-mqtt", clean_session=True)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

def mqtt_connect():
    while True:
        try:
            client.connect(MQTT_HOST, MQTT_PORT, 60)
            client.loop_start()
            return
        except Exception as e:
            print(f"[MQTT] connect failed: {e}; retrying in 2s", flush=True)
            time.sleep(2)

mqtt_connect()

def publish(payload: str):
    try:
        client.publish(MQTT_TOPIC, payload, qos=0, retain=False)
    except Exception as e:
        print(f"[MQTT] publish error: {e}", flush=True)

# ---- Hardware ----
# RotaryEncoder: counts up/down. Many EC11 give 4 edges per detent; gpiozero normalizes steps per edge.
encoder = RotaryEncoder(a=GPIO_CLK, b=GPIO_DT, max_steps=0)  # unbounded
button = Button(GPIO_SW, pull_up=True, bounce_time=DEBOUNCE_MS/1000.0)

last_steps = 0

def on_rotate():
    global last_steps
    steps = encoder.steps
    print(f"[rotary] steps: {steps}, delta: {steps - last_steps}")
    delta = steps - last_steps
    last_steps = steps
    if delta > 0:
        publish(f"brightness_up:{STEP_PCT}")
    elif delta < 0:
        publish(f"brightness_down:{STEP_PCT}")

def on_press():
    print("[rotary] button pressed")
    publish("toggle")

encoder.when_rotated = on_rotate
button.when_pressed = on_press

# ---- Graceful exit ----
def cleanup(signum=None, frame=None):
    try:
        client.loop_stop()
        client.disconnect()
    finally:
        sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

print("[rotary] running; rotate to send up/down, press to toggle")
while True:
    time.sleep(1)
