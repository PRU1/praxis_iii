"""
File: initial_hall_effect_test.py

Description:
This module implements an initial test for the hall effect sensor.

Author: Jadon Tsai
Date: 2026-03-21
"""
import time
import board
import digitalio

hall = digitalio.DigitalInOut(board.GP15)
hall.direction = digitalio.Direction.INPUT

last_state = hall.value

print("OUT =", "HIGH" if last_state else "LOW")

while True:
    state = hall.value

    if state:
        print("HIGH")
    else:
        print("LOW")

    time.sleep(0.01)
