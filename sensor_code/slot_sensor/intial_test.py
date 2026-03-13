import time
import board
import digitalio

sensor = digitalio.DigitalInOut(board.GP15)
sensor.direction = digitalio.Direction.INPUT
sensor.pull = digitalio.Pull.UP

while True:
    if sensor.value:
        print("Beam blocked")
    else:
        print("Beam clear")
    time.sleep(0.1)
