from gpiozero import RotaryEncoder, Button
from gpiozero.pins.pigpio import PiGPIOFactory
import paho.mqtt.client as mqtt

Device.pin_factory = PiGPIOFactory()

mqttc = mqtt.Client()
mqttc.connect("localhost", 1883, 60)

encoder = RotaryEncoder(a=17, b=18, max_steps=100)
button = Button(27)

def rotate():
    if encoder.steps > 0:
        print("CW")
        mqttc.publish("home/rotary/light", "brightness_up")
    else:
        print("CCW")
        mqttc.publish("home/rotary/light", "brightness_down")

def press():
    print("Button pressed")
    mqttc.publish("home/rotary/light", "toggle")

encoder.when_rotated = rotate
button.when_pressed = press

mqttc.loop_forever()
