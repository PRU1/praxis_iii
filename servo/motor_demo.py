"""
File: motor_demo.py

Description:
This module tests the functionality of multiple motors at once.
This is an initial working test, so no specifications are tested.

Author: Jadon Tsai
Date: 2026-03-26
"""
import time
import board
import pwmio
from adafruit_motor import servo

# declaring variables
pwm1 = pwmio.PWMOut(board.GP0, duty_cycle=2**15, frequency=50)
pwm2 = pwmio.PWMOut(board.GP1, duty_cycle=2**15, frequency=50)
pwm3 = pwmio.PWMOut(board.GP2, duty_cycle=2**15, frequency=50)

servo_motor1 = servo.Servo(pwm1)
servo_motor2 = servo.Servo(pwm2)
servo_motor3 = servo.Servo(pwm3)

#180 is full closed angle, turns ccw from 0 to 180
#110 is full open angle
def calibration():
    """
    Sets all the motor angles to a known angle, so that we can then 
    attach the servo arms
    """
    servo_motor1.angle = 180
    time.sleep(2)
    servo_motor2.angle = 180
    time.sleep(2)
    servo_motor3.angle = 180
    time.sleep(2)

def testing():
    servo_motor2.angle = 180

def demo():
    """
    Moving servos simultaneously from
    full open position (110 degrees)
    to full closed (180 degrees)
    """
    time.sleep(1)
    servo_motor1.angle = 110
    servo_motor2.angle = 110
    servo_motor3.angle = 110
    time.sleep(2)

    servo_motor1.angle = 180
    servo_motor2.angle = 180
    servo_motor3.angle = 180

if __name__ == '__main__':
    #calibration()
    demo()
    



    

