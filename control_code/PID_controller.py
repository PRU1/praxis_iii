import time
import math
import board
import busio
import pwmio
import digitalio

from adafruit_as726x import AS726x_I2C
from adafruit_motor import servo
import adafruit_am2320

#pins
HALL_PIN = board.GP15
MOTOR_PIN_1 = board.GP0
MOTOR_PIN_2 = board.GP5
MOTOR_PIN_3 = board.GP9
MOTOR_PIN_4 = board.GP14
i2c = busio.I2C(board.GP17, board.GP16)
#i2c_indoor = busio.I2C(board.GP6, board.GP7)#need this bc we have two temp sensors

#ctrl variables
TARGET_APPARENT_C = 23.0
CONTROL_PERIOD_S = 3.0
DEADBAND_C = 0.4

#servo variables
SERVO_CLOSE = 180
SERVO_OPEN = 110
SERVO_MIN = 70

#geometry variables
SIDE_ANGLES = {1:0, 2:90, 3:180, 4:270}
WIND_SPEED_FRAC = 0.3


def apparent_temperature_c(temp_c, rh_percent, wind_m_s):
    #Australian apparent temperature calculation
    rh = rh_percent / 100.0 #humidity
    vapor_pressure_hpa = rh * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))
    return temp_c + 0.33 * vapor_pressure_hpa - 0.70 * wind_m_s - 4.0

#helper functions
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x

def circular_diff_deg(a, b):
    d = (a - b + 180.0) % 360.0 - 180.0
    return d

def side_exposure(side_deg, wind_from):
    diff = abs(circular_diff_deg(side_deg, wind_from))
    return (math.cos(math.radians(diff))+1)/2.0

#mode check
def ventilation_mode(indoor_at, outdoor_at, target_at, deadband):
    if indoor_at > target_at + deadband:
        if outdoor_at < indoor_at:
            return "cool"
        return "hold"

    if indoor_at < target_at - deadband:
        if outdoor_at > indoor_at:
            return "warm"
        return "hold"

    return "hold"

class PID:
    def __init__(self, kp, ki, kd, out_min=0.0, out_max=1.0, int_min = 0, int_max = 10):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.out_min = out_min
        self.out_max = out_max
        self.integral_min = int_min
        self.integral_max = int_max 

        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_t = None

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_t = None

    def update(self, setpoint, measurement):
        now = time.monotonic()
        error = setpoint - measurement

        if self.prev_t is None:
            dt = 0.0
        else:
            dt = now - self.prev_t

        derivative = 0.0
        if dt > 0:
            self.integral += error * dt
            self.integral = clamp(self.integral, self.integral_min, self.integral_max)
            derivative = (error - self.prev_error) / dt

        output = (
            self.kp * error +
            self.ki * self.integral +
            self.kd * derivative
        )
        output = clamp(output, self.out_min, self.out_max)

        self.prev_error = error
        self.prev_t = now
        return output


class ServoInit:
    def __init__(self, pin):
        self.pwm = pwmio.PWMOut(pin, duty_cycle=2**15, frequency=50)
        self.servo = servo.Servo(self.pwm)
        self.closed_angle = SERVO_CLOSE
        self.open_angle = SERVO_OPEN

    def move(self, angle):
        angle = clamp(angle, SERVO_MIN, SERVO_CLOSE)
        self.servo.angle =angle
        
    def set_fraction(self, fraction): #might delete later
        fraction = clamp(fraction, 0.0, 1.0)
        angle = self.closed_angle + (self.open_angle - self.closed_angle) * fraction
        self.move(angle)

class ServoControl:
    def __init__(self):
        self.set = {1: ServoInit(MOTOR_PIN_1),
                    2: ServoInit(MOTOR_PIN_2), 
                    3: ServoInit(MOTOR_PIN_3), 
                    4: ServoInit(MOTOR_PIN_4)}
    
    def set_sides(self, set1):
        for side, value in set1.items():
            self.set[side].set_fraction(value)

    def calibrate(self): #also doubles as close all
        for side in self.set:
            self.set[side].move(SERVO_CLOSE)

class WindSpeedSensor:
    def __init__(self, pin):
        self.hall = digitalio.DigitalInOut(pin)
        self.hall.direction = digitalio.Direction.INPUT
        self.last_state = self.hall.value
        self.counts = 0
        self.last_calc_time = time.monotonic()
        self.wind_speed = 0.0

    def update(self):
        state = self.hall.value
        if state and not self.last_state:
            self.counts += 1
        self.last_state = state

    def read_speed(self):
        now = time.monotonic()
        dt = now - self.last_calc_time
        if dt <= 0:
            return self.wind_speed

        rps = (self.counts / 2.0) / dt
        self.wind_speed = (rps / 0.8457) * 3.8

        self.counts = 0
        self.last_calc_time = now
        return self.wind_speed



class WindDirectionSensor:
    def __init__(self):
        # i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
        self.sensor = AS726x_I2C(i2c)
        self.sensor.conversion_mode = self.sensor.MODE_2
        self.readings = [[61.2825, 83.7207, 101.519, 222.273, 337.877, 29.581],
            [95.6008, 170.542, 178.119, 202.24, 200.319, 24.848],
            [79.6673, 93.023, 84.9066, 95.3963, 105.748, 21.2983],
            [41.6721, 25.8397, 20.3038, 21.9411, 26.6518, 26.0313],
            [34.3182, 19.6382, 19.3809, 23.8491, 33.5297, 31.9475],
            [28.19, 19.6382, 22.1496, 40.0664, 58.4621, 26.0313],
            [24.513, 20.6718, 28.6098, 86.8106, 144.436, 28.3977],
            [30.6413, 28.9405, 44.2991, 157.404, 297.469, 26.0313]]
        
    def dotProductLength6(self, a, b):
        value = 0
        for i in range(6):
            value = value + a[i]*b[i]
        return value
    
    def getSimilarity(self, a, bs):
        max = -1;
        ind = 0;
        for i in range(len(bs)):
            b = bs[i];
            similarity = self.dotProductLength6(a, b) / (self.dotProductLength6(a, a)*self.dotProductLength6(b, b))**0.5
            if similarity > max:
                max = similarity
                ind = i
        return ind
    
    def getangle(self):
        list = [self.sensor.blue, self.sensor.green, self.sensor.yellow, self.sensor.orange, self.sensor.red, self.sensor.violet]
        print(list)
        angle = self.getSimilarity(list, self.readings) * 45
        return angle

    def read_features(self):
        while not self.sensor.data_ready:
            time.sleep(0.1)
        angle = self.getangle()
        time.sleep(2)
        return angle

class TemperatureSensor:
    def __init__(self, i2c):
        self.sensor = adafruit_am2320.AM2320(i2c)

    def read(self):
        try:
            temperature = self.sensor.temperature
            time.sleep(0.2) 
            humidity = self.sensor.relative_humidity
            return temperature, humidity
        except Exception as e:
            print("Read error:", repr(e))
            return None, None
        
#fix depending on granularity
def choose_window_openings(total_open, wind_from_deg):
    exposures = {
        side: side_exposure(angle, wind_from_deg)
        for side, angle in SIDE_ANGLES.items()
    }

    windward = max(exposures, key=exposures.get)
    leeward = min(exposures, key=exposures.get)
    
    temp_set =  {
        1: 0.0,
        2: 0.0,
        3: 0.0,
        4: 0.0,
    }
    temp_set[windward] = total_open
    temp_set[leeward] = total_open
    for side in temp_set:
        temp_set[side] = clamp(temp_set[side], 0, 1)

    return temp_set, windward, leeward

class ActualController:
    def __init__(self, indoor_sensor, outdoor_sensor, wind_speed_sensor, wind_direction_sensor, servo_controller):
        self.indoor_sensor = indoor_sensor
        self.outdoor_sensor = outdoor_sensor
        self.wind_speed_sensor = wind_speed_sensor
        self.wind_direction_sensor = wind_direction_sensor
        self.servo_controller = servo_controller
        self.target_at = TARGET_APPARENT_C
        self.vent_pid = PID(
            kp=0.18,
            ki=0.03,
            kd=0.02,
            out_min=0.0,
            out_max=1.0,
            integral_min=-10.0,
            integral_max=10.0,
        )
    def step(self):
        indoor_temp, indoor_humid = (30, 30)
        outdoor_temp, outdoor_humid = (20, 20)

        if None in (indoor_temp, indoor_humid, outdoor_temp, outdoor_humid):
            print("Sensor missed")
            return    
        wind_speed = 5
        wind_from_deg = self.wind_direction_sensor.read_features()

        indoor_air_speed = 5 #need a number here
        outdoor_air_speed = 5
        indoor_at = apparent_temperature_c(indoor_temp, indoor_humid, indoor_air_speed)
        outdoor_at = apparent_temperature_c(outdoor_temp, outdoor_humid, outdoor_air_speed)
        
        mode = ventilation_mode(indoor_at, outdoor_at, self.target_at, DEADBAND_C)

        if mode == "cool":
            total_open = self.vent_pid.update(indoor_at, self.target_at)
            openings, windward, leeward = choose_window_openings(total_open, wind_from_deg)
        else:
            self.vent_pid.reset()
            openings = {1: 0, 2: 0, 3: 0, 4: 0}
            windward = None
            leeward = None

        self.servo_controller.set_sides(openings)
        
        #print console, can delete
        print("Mode:", mode)

        print("Indoor: T={:.2f}C Humidity={:.1f}% Apparently at={:.2f}C".format(
            indoor_temp, indoor_humid, indoor_at
        ))
        print("Outdoor: T={:.2f}C Humidity={:.1f}% Apparently at={:.2f}C".format(
            outdoor_temp, outdoor_humid, outdoor_at
        ))
        print("Wind: {:.2f} m/s from {:.1f} deg".format(wind_speed, wind_from_deg))
        print("Windward:", windward, "Leeward:", leeward)
        print("========================================================")

def main():
    inside_temp_sens = 0
    outside_temp_sens = 0
    wind_speed_sens = WindSpeedSensor(HALL_PIN)
    wind_direction_sens = WindDirectionSensor()
    servo_controller1 = ServoControl()

    pid_controller = ActualController(indoor_sensor=inside_temp_sens,
                                      outdoor_sensor=outside_temp_sens,
                                      wind_speed_sensor=wind_speed_sens,
                                      wind_direction_sensor = wind_direction_sens,
                                      servo_controller=servo_controller1)
    
    servo_controller1.calibrate()#close if broken
    last_control = time.monotonic()
    while True:
        wind_speed_sens.update()

        now = time.monotonic()
        if now - last_control >= CONTROL_PERIOD_S:
            pid_controller.step()
            last_control = now

        print("========================================================================")
        time.sleep(CONTROL_PERIOD_S)

if __name__ == '__main__':
    main()

