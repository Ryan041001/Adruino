import Adafruit_DHT as DHT
import RPi.GPIO as GPIO
import time
import datetime

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(0)

# Hardware settings
DHT_TYPE, DHT_PIN = DHT.DHT11, 4
PINS = {'LED':17, 'BUZZER':27, 'FAN':22}
THRESHOLDS = {'T_HIGH':20, 'T_LOW':10, 'HUMIDITY':70}

# GPIO setup
GPIO.setup(list(PINS.values()), GPIO.OUT)
buzzer = GPIO.PWM(PINS['BUZZER'], 1000)
buzzer.start(0)

def display_status(t, h, fan, alarm):
    """Display system status"""
    print(f"""
========================================
 Raspberry Pi Environment Monitor
========================================
 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
----------------------------------------
 Temperature: {t:.1f}C | Humidity: {h:.1f}%
----------------------------------------
 Fan: {'ON' if fan else 'OFF'} | Alarm: {'TRIGGERED' if alarm else 'Normal'}
========================================""")
    
try:
    while True:
        h, t = DHT.read_retry(DHT_TYPE, DHT_PIN)
        if None not in (h, t):
            # Determine alarm conditions
            temp_high = t > THRESHOLDS['T_HIGH']
            temp_low = t < THRESHOLDS['T_LOW']
            humid_high = h > THRESHOLDS['HUMIDITY']
            alarm = any([temp_high, temp_low, humid_high])
            
            # Activate fan only if temperature is too high
            fan_on = temp_high
            
            GPIO.output(PINS['LED'], alarm)
            GPIO.output(PINS['FAN'], not fan_on)
            buzzer.ChangeDutyCycle(50 * alarm)
            display_status(t, h, fan_on, alarm)
        time.sleep(2)
except Exception as e:
    print(f"Error: {str(e)}")
except KeyboardInterrupt:
    print("\nSystem shutdown...")
finally:
    buzzer.stop()
    GPIO.cleanup()