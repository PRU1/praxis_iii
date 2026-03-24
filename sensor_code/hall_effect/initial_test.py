import time
import board
import digitalio

hall = digitalio.DigitalInOut(board.GP15)
hall.direction = digitalio.Direction.INPUT

last_state = hall.value

print("AH372 ready")
print("OUT =", "HIGH" if last_state else "LOW")

while True:
    state = hall.value

    if state:
        print("HIGH")
    else:
        print("LOW")

    time.sleep(0.01)
