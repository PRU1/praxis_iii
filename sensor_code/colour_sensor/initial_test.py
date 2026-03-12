import time
import board
import busio
from adafruit_as726x import AS726x_I2C

#Graph scaling (for later)
max_val = 16000
max_graph = 80

def graph_map(x):
    return min(int(x * max_graph / max_val), max_graph)

#create I2C on Pico pins CHANGE PINS HERE IF YOURE USING A DIFFERENT PIN
i2c = busio.I2C(board.GP1, board.GP0)

#wait for I2C
while not i2c.try_lock():
    pass
print("I2C devices:", [hex(x) for x in i2c.scan()])
i2c.unlock()

#create sensor object
sensor = AS726x_I2C(i2c)

sensor.conversion_mode = sensor.MODE_2
#turns lights on, kinda bright rn
sensor.driver_led = True
sensor.indicator_led = True

print("AS7262 ready")

while True:

    while not sensor.data_ready:
        time.sleep(0.05)

    print('Temperature: {0}C'.format(sensor.temperature)) #should be around 30
  #prints numerical values, need to scale later
    print("V:", sensor.violet)
    print("B:", sensor.blue)
    print("G:", sensor.green)
    print("Y:", sensor.yellow)
    print("O:", sensor.orange)
    print("R:", sensor.red)

    time.sleep(1)
