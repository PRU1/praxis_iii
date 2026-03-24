import time
import board
import busio
import adafruit_am2320

time.sleep(1.0) 

i2c = busio.I2C(board.GP1, board.GP0)
sensor = adafruit_am2320.AM2320(i2c)

while True:
    try:
        temperature = sensor.temperature
        time.sleep(0.2)  
        humidity = sensor.relative_humidity

        print(f"Temperature: {temperature:.1f} C")
        print(f"Humidity: {humidity:.1f} %")
        print("---------------------------")

    except Exception as e:
        print("Read error:", repr(e))

    time.sleep(3)
