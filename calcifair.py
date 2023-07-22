# -*- coding: utf-8 -*-

import socket
from getmac import get_mac_address
import logging
from PIL import ImageFont, ImageDraw, Image
from functools import wraps
import sys
import time
from time import gmtime, strftime
import os.path
from datetime import datetime, timedelta, timezone
import dateutil.parser
import yaml
import json
import requests
import threading
import board
import busio
import adafruit_sgp30
from adafruit_bme280 import basic as adafruit_bme280
from ltr559 import LTR559
import ST7789
from setproctitle import setproctitle
import psutil
from pprint import pprint
import random
from inc.time import *
from paho.mqtt import client as mqtt_client


def checkIfProcessRunning(processName):
    '''
    Check if there is any running process that contains the given name processName.
    https://thispointer.com/python-check-if-a-process-is-running-by-name-and-find-its-process-id-pid/
    '''
    #Iterate over the all the running process
    for proc in psutil.process_iter():
        try:
            # Check if process name contains the given name string.
            if processName.lower() in proc.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


# Check if any chrome process was running or not.
if checkIfProcessRunning('calcifair-main'):
    print("🔥 Calcifer is awake already")
    exit()

setproctitle('calcifair-main')

dir_path = os.path.dirname(os.path.realpath(__file__))

# Load configuration file
config = None
file_config = os.path.join(dir_path, 'config.yaml')

with open(file_config) as file:
    config = yaml.full_load(file)

# logging.basicConfig(filename='logs/python.txt')

# Set up CO2 & VOC sensor
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

# Set up BME280 temperature, humidity and pressure sensor
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c, address=0x76)
# Source: https://meteologix.com/al/model-charts/euro/comunidad-de-madrid/sea-level-pressure.html
bme280.sea_level_pressure = 1020

# Set up light and proximity sensor
ltr559 = LTR559()

# Set up screen
disp = ST7789.ST7789(
    port=0,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=19,               # 18 for back BG slot, 19 for front BG slot.
    spi_speed_hz=80 * 1000 * 1000
)
WIDTH = disp.width
HEIGHT = disp.height

# Air quality levels
# From Hong Kong Indoor Air Quality Management Group
# https://www.iaq.gov.hk/media/65346/new-iaq-guide_eng.pdf

# CO2 levels in ppm
LIMIT_ECO2_BAD = 1000
LIMIT_ECO2_MEDIUM = 800

# VOC levels in ppb
LIMIT_TVOC_BAD = 261
LIMIT_TVOC_MEDIUM = 87

# AQI levels
LIMIT_AQI_BAD = 100
LIMIT_AQI_MEDIUM = 50

def turn_off_display():
    disp.set_backlight(0)


def turn_on_display():
    disp.set_backlight(1)


# Initialize display.
disp.begin()


# Load emoji while starts
image_path = os.path.join(dir_path, 'assets/emoji-fire.png')
image = Image.open(image_path)
disp.display(image)

# Calcifer says hi
print("🔥 Calcifer is waking up, please wait...")
# print("SGP30 serial #", [hex(i) for i in sgp30.serial])


def calcifer_expressions(expression, seconds = 5):
    image_path = None

    try:
        image_path = os.path.join(dir_path, 'assets/calcifer-' + expression + '.gif')
        image = Image.open(image_path)

        timeout = time.time() + 5 # 5 seconds from now
        while True:
            if time.time() > timeout:
                break
            
            frame = 0

            while frame < image.n_frames:
                try:
                    image.seek(frame)
                    disp.display(image.resize((WIDTH, HEIGHT)))
                    frame += 1
                    time.sleep(0.05)
                except EOFError:
                    frame = 0
    except:
        print('Calcifer expression not found')


def air_quality():
    global sgp30
    if sgp30:
        if sgp30.eCO2 and sgp30.TVOC:
            if sgp30.eCO2 > 1000 or sgp30.TVOC > 261:
                sgp30.air_quality = "bad"
            elif sgp30.eCO2 > 800 or sgp30.TVOC > 87:
                sgp30.air_quality = "medium"
            else:
                sgp30.air_quality = "good"
        else:
            sgp30.air_quality = "unknown"


screen_timeout = 0
start_time = datetime.now(timezone.utc)

# Initialise air quality sensor
sgp30.iaq_init()

# Load air quality sensor baseline from config file
baseline_eCO2_restored, baseline_TVOC_restored, baseline_timestamp = None, None, None
if config['sgp30_baseline']['timestamp'] is not None:
    baseline_timestamp = config['sgp30_baseline']['timestamp']

    # Ignore stored baseline if older than a week
    if datetime.now(timezone.utc) < baseline_timestamp + timedelta(days=7):
        baseline_eCO2_restored = config['sgp30_baseline']['eCO2']
        baseline_TVOC_restored = config['sgp30_baseline']['TVOC']

        print('Stored baseline is recent enough: 0x{:x} 0x{:x} | {}'.format(
            baseline_eCO2_restored,
            baseline_TVOC_restored,
            readable_log_time(baseline_timestamp)))

        # Set baseline
        sgp30.set_iaq_baseline(
            baseline_eCO2_restored, baseline_TVOC_restored)
    else:
        print('Stored baseline is too old')

# Calculate https://www.cactus2000.de/uk/unit/masshum.shtml
# sgp30.set_iaq_humidity(7.5666)

try:
    result_log = os.path.join(dir_path, 'logs/sgp30-result.txt')
    baseline_log = os.path.join(dir_path, 'logs/sgp30-baseline.txt')
    iqair_log = os.path.join(dir_path, 'logs/iqair.txt')
except:
    print('Error creating log files')

baseline_log_counter = datetime.now(timezone.utc) + timedelta(minutes=10)

# If there are not baseline values stored, wait 12 hours before saving every hour
if baseline_eCO2_restored is None or baseline_TVOC_restored is None:
    baseline_log_counter_valid = datetime.now(timezone.utc) + timedelta(hours=12)
    print('Calcifer will store a valid baseline in 12 hours')
else:
    baseline_log_counter_valid = datetime.now(timezone.utc) + timedelta(hours=1)

# External air quality provided by AirVisual (IQAir)
# Based on US EPA National Ambient Air Quality Standards https://support.airvisual.com/en/articles/3029425-what-is-aqi
# <50, Good; 51-100, Moderate (ventilation is discouraged); >101, Unhealthy

iqair_query = 'https://api.airvisual.com/v2/nearest_city?lat={}&lon={}&key={}'.format(
    config['location']['latitude'], config['location']['longitude'], config['iqair']['token'])
iqair_result, iqair_current = None, {}

print(iqair_query)

def update_iqair_result():
    global iqair_result, iqair_query, iqair_current
    iqair_result = requests.get(iqair_query)
    iqair_result = iqair_result.json()
    
    if iqair_result['status'] == 'success':
        iqair_results_current = iqair_result['data']['current']

        iqair_current['temp'] = iqair_results_current['weather']['tp']
        iqair_current['pressure'] = iqair_results_current['weather']['pr']
        iqair_current['humidity'] = iqair_results_current['weather']['hu']
        iqair_current['weather_timestamp'] = dateutil.parser.parse(iqair_results_current['weather']['ts'])

        iqair_current['aqi'] = iqair_results_current['pollution']['aqius']
        iqair_current['pollution_timestamp'] = dateutil.parser.parse(
        iqair_results_current['pollution']['ts'])

        iqair_message = "Outdoors: {}°C, {} hPa, {}% RH, AQI {} | Data time: {} | Log time: {}".format(
            iqair_current['temp'],
            iqair_current['pressure'],
            iqair_current['humidity'],
            iqair_current['aqi'],
            readable_log_time( iqair_current['pollution_timestamp'] ),
            datetime.now().strftime(readable_time_format) )

        print(iqair_message)
        
        # Log iqair results
        with open(iqair_log, 'a') as file:
            file.write(iqair_message + '\n')
        
        return
    else:
        print("AirVisual API error: {}".format(iqair_result['status']))
        print(iqair_query)

    threading.Timer(1800.0, update_iqair_result).start()

update_iqair_result()

# for MQTT

# Get local IP
# https://tecadmin.net/python-how-to-find-local-ip-address/
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


local_ip = get_local_ip()

# from https://github.com/ironsheep/RPi-Reporter-MQTT2HA-Daemon/blob/8fbb4f140ad722f8779bc61bd7dadb79f63f0423/ISP-RPi-mqtt-daemon.py
# what RPi device are we on?
# get our hostnames so we can setup MQTT
# this will fill-in rpi_mac

rpi_mac = get_mac_address()
print(rpi_mac)

mac_basic = rpi_mac.lower().replace(":", "")
mac_left = mac_basic[:6]
mac_right = mac_basic[6:]
print('mac lt=[{}], rt=[{}], mac=[{}]'.format(
    mac_left, mac_right, mac_basic))
uniqID = "RPi-{}Mon{}-calcifair".format(mac_left, mac_right)

mqtt_connected = False  # global variable for the state of the connection

mqtt_client_id = "homeassistant"
mqtt_broker = local_ip
mqtt_port = config['mqtt']['port']
mqtt_username = config['mqtt']['username']
mqtt_password = config['mqtt']['password']


def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
        else:
            print("Failed to connect to MQTT broker, return code %d\n", rc)

    client = mqtt_client.Client(mqtt_client_id)
    client.username_pw_set(mqtt_username, mqtt_password)
    client.on_connect = on_connect
    client.connect(mqtt_broker, mqtt_port)
    return client


def publish_mqtt(topic, msg, retain=False):
    global mqtt

    topic = mqtt_client_id + "/" + topic

    msg = f"{msg}"
    result = mqtt.publish(topic, msg, retain=retain)

    status = result[0]
    if status != 0:
        print(f"Failed to send message to topic {topic}")


mqtt = connect_mqtt()
mqtt.loop_start()

# Configuration topics and payloads
mqtt_eco2_config = {
    "uniq_id": f"{uniqID}_co2",
    "name": "CO2",
    "device_class": "carbon_dioxide",
    "state_topic": f"{mqtt_client_id}/sensor/calcifair/state",
    "unit_of_measurement": "ppm",
    "value_template": "{{ value_json.eco2 }}",
    "dev": {
        "identifiers": [uniqID],
        "name": "Calcifair"
    }
}

mqtt_tvoc_config = {
    "uniq_id": f"{uniqID}_voc",
    "name": "VOC",
    "device_class": "volatile_organic_compounds",
    "state_topic": f"{mqtt_client_id}/sensor/calcifair/state",
    "unit_of_measurement": "ppb",
    "value_template": "{{ value_json.tvoc }}",
    "pl_avail": "online",
    "pl_not_avail": "offline",
    "dev": {
        "identifiers": [uniqID],
        "name": "Calcifair"
    }
}

mqtt_lux_config = {
    "uniq_id": f"{uniqID}_lux",
    "name": "Light",
    "device_class": "illuminance",
    "state_topic": f"{mqtt_client_id}/sensor/calcifair/state",
    "unit_of_measurement": "lx",
    "value_template": "{{ value_json.lux }}",
    "pl_avail": "online",
    "pl_not_avail": "offline",
    "dev": {
        "identifiers": [uniqID],
        "name": "Calcifair"
    }
}

mqtt_temperature_config = {
    "uniq_id": f"{uniqID}_temperature",
    "name": "Temperature",
    "device_class": "temperature",
    "state_topic": f"{mqtt_client_id}/sensor/calcifair/state",
    "unit_of_measurement": "°C",
    "value_template": "{{ value_json.temperature }}",
    "pl_avail": "online",
    "pl_not_avail": "offline",
    "dev": {
        "identifiers": [uniqID],
        "name": "Calcifair"
    }
}

mqtt_humidity_config = {
    "uniq_id": f"{uniqID}_humidity",
    "name": "Humidity",
    "device_class": "humidity",
    "state_topic": f"{mqtt_client_id}/sensor/calcifair/state",
    "unit_of_measurement": "%",
    "value_template": "{{ value_json.humidity }}",
    "pl_avail": "online",
    "pl_not_avail": "offline",
    "dev": {
        "identifiers": [uniqID],
        "name": "Calcifair"
    }
}

publish_mqtt("sensor/calcifair/eco2/config", json.dumps(mqtt_eco2_config), retain=True)
publish_mqtt("sensor/calcifair/tvoc/config", json.dumps(mqtt_tvoc_config), retain=True)
publish_mqtt("sensor/calcifair/lux/config", json.dumps(mqtt_lux_config), retain=True)
publish_mqtt("sensor/calcifair/temperature/config", json.dumps(mqtt_temperature_config), retain=True)
publish_mqtt("sensor/calcifair/humidity/config", json.dumps(mqtt_humidity_config), retain=True)

def send_to_mqtt():
    global bme280, sgp30, ltr559

    state = {
        "timestamp": datetime.now().isoformat(),
        "eco2": sgp30.eCO2,
        "tvoc": sgp30.TVOC,
        "temperature": "{:0.1f}".format(bme280.temperature),
        "humidity": "{:0.0f}".format(bme280.humidity),
        "baseline_eco2": sgp30.baseline_eCO2,
        "baseline_tvoc": sgp30.baseline_TVOC,
        "lux": "{:0.1f}".format( ltr559.get_lux() )
    }
    
    publish_mqtt("sensor/calcifair/state", json.dumps(state))

    # print(result_human)
    print("Readings published via MQTT")

    threading.Timer(30.0, send_to_mqtt).start()


def send_to_mqtt_run():
    global aio, bme280, sgp30, ltr559
    # Start sending data to MQTT after 3 min
    threading.Timer(30.0, send_to_mqtt).start()


send_to_mqtt_run()

# Wait while sensor warms up
warmup_counter = datetime.now(timezone.utc) + timedelta(seconds=30)
while datetime.now(timezone.utc) < warmup_counter:
    if sgp30.eCO2 > 400 and sgp30.TVOC > 0:
        break
    time.sleep(1)

checking_good = False
checking_good_count = 0
checking_bad = False
checking_bad_count = 0
background_img = None
proximity_count = 0

while True:
    air_quality()

    # Get proximity
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
    # print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

    # Get air quality
    # https://mkaz.blog/code/python-string-format-cookbook/
    result_human = 'CO2: {} ppm, VOC: {} ppb, Lux: {:.1f} lx | {:.1f}°C, {:.0f} hPa, {:.1f}% RH | {}'.format(
        sgp30.eCO2,
        sgp30.TVOC,
        lux,
        bme280.temperature,
        bme280.pressure,
        bme280.humidity,
        datetime.now().strftime(readable_time_format))

    # Log baseline
    baseline_human = 'CO2: {0} 0x{0:x}, VOC: {1} 0x{1:x} | {2}'.format(
        sgp30.baseline_eCO2,
        sgp30.baseline_TVOC,
        datetime.now().strftime(readable_time_format))

    if datetime.now(timezone.utc) > baseline_log_counter:
        with open(result_log, 'a') as file:
            file.write(result_human + '\n')

    if datetime.now(timezone.utc) > baseline_log_counter_valid:
        baseline_log_counter_valid = datetime.now(timezone.utc) + timedelta(hours=1)
        print("Valid baseline: " + baseline_human)
        with open(baseline_log, 'a') as file:
            file.write("Valid: " + baseline_human + '\n')

        # Store new valid baseline
        config['sgp30_baseline']['eCO2'] = sgp30.baseline_eCO2
        config['sgp30_baseline']['TVOC'] = sgp30.baseline_TVOC
        config['sgp30_baseline']['timestamp'] = datetime.now(timezone.utc)

        with open(file_config, 'w') as file:
            yaml.dump(config, file)
            print('Baseline updated on config file')

    elif datetime.now(timezone.utc) > baseline_log_counter:
        baseline_log_counter = datetime.now(timezone.utc) + timedelta(minutes=10)

        print("Baseline: " + baseline_human)
        with open(baseline_log, 'a') as file:
            file.write(baseline_human + '\n')

    # Screen alerts
    if prox >= 5:
        screen_timeout = 10  # seconds the screen will stay on
        proximity_count += 1
    else:
        proximity_count = 0

    # What to show if screen on over 3 seconds
    if proximity_count >= 3:
        turn_on_display()

        expressions = ['idle', 'talks']
        expression = random.choice(expressions)
        calcifer_expressions(expression)
        proximity_count == 0

    # What to show immediately
    if prox >= 5 or screen_timeout > 0:
        screen_timeout -= 1

        turn_on_display()

        color = (255, 255, 255)
        background_color = (0, 0, 0)

        # Animated background
        if ( background_img == 'background.png' ):
            background_img = 'background-alt.png'
        else:
            background_img = 'background.png'

        image_path = os.path.join(
            dir_path, 'assets/', background_img)
        img = Image.open(image_path)

        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
        font_small = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)

        draw.rectangle((0, 0, disp.width, 80), background_color)

        draw.text((10, 10), 'CO2', font=font, fill=color)
        if (sgp30.eCO2 <= 400):
            draw.text((10, 45), '<400', font=font_bold, fill=color)
        else:
            draw.text((10, 45), str(sgp30.eCO2), font=font_bold, fill=color)
        draw.text((10, 80), 'ppm', font=font, fill=color)

        draw.text((125, 10), 'VOC', font=font, fill=color)
        draw.text((125, 45), str(sgp30.TVOC), font=font_bold, fill=color)
        draw.text((125, 80), 'ppb', font=font, fill=color)

        # Rather accessible traffic lights from https://uxdesign.cc/beautiful-accessible-traffic-light-colors-b2b14a102a38
        green = (125, 142, 40)
        yellow = (252, 202, 67)
        red = (171, 7, 48)

        color_eCO2 = green
        if (sgp30.eCO2 >= LIMIT_ECO2_BAD):
            color_eCO2 = red
        elif (sgp30.eCO2 >= LIMIT_ECO2_MEDIUM):
            color_eCO2 = yellow

        draw.text((10, 120), '●', font=font, fill=color_eCO2)

        color_TVOC = green
        if (sgp30.TVOC >= LIMIT_TVOC_BAD):
            color_TVOC = red
        elif (sgp30.TVOC >= LIMIT_TVOC_MEDIUM):
            color_TVOC = yellow

        color_AQI = green
        if (iqair_current['aqi'] >= LIMIT_AQI_BAD):
            color_AQI = red
        elif (iqair_current['aqi'] >= LIMIT_AQI_MEDIUM):
            color_AQI = yellow
        
        draw.text((125, 120), '●', font=font, fill=color_TVOC)

        draw.text((125, 160), '■', font=font_small, fill=color_AQI)
        draw.text((148, 160), 'AQI ' + str(iqair_current['aqi']), font=font_small, fill=color)

        draw.text((125, 185), str(
            iqair_current['temp']) + '°C', font=font_small, fill=color)
        draw.text((125, 210), str(iqair_current['humidity']) + '% RH', font=font_small, fill=color)

        disp.display(img)
    else:
        turn_off_display()


    # print(result_human)
    time.sleep(1.0)
