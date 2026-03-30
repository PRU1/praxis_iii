"""
File: 
window_reliability_testing.py

Description:
This module implements tests the reliability of the window slats 
as per specificaiton P-S.4

Author: Jadon Tsai
Date: 2026-03-28
"""
import time
import board
import pwmio
from adafruit_motor import servo

pwm1 = pwmio.PWMOut(board.GP0, duty_cycle=2**15, frequency=50)

servo_motor1 = servo.Servo(pwm1)


def testing():
    """
    This function is designed to simulate opening and closing of the 
    slats 100 times, at both extreme angles (note that this is different
    than the original code as we made slight modifications to the servo arm.
    """
    for i in range(99):
        servo_motor1.angle = 40
        time.sleep(1)
        servo_motor1.angle = 160
        time.sleep(1)


if __name__ == '__main__':
    testing()
