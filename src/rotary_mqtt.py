from gpiozero import RotaryEncoder, Button

encoder = RotaryEncoder(a=17, b=18, max_steps=100)
button = Button(27)

def rotate():
    if encoder.steps > 0:
        print("CW")
    else:
        print("CCW")

def press():
    print("Button pressed")

encoder.when_rotated = rotate
button.when_pressed = press

