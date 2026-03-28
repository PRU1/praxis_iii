import time
import board
import pwmio
from adafruit_motor import servo

pwm1 = pwmio.PWMOut(board.GP0, duty_cycle=2**15, frequency=50)

servo_motor1 = servo.Servo(pwm1)


def testing():
    for i in range(99):
        servo_motor1.angle = 40
        time.sleep(1)
        servo_motor1.angle = 160
        time.sleep(1)


if __name__ == '__main__':
    testing()
