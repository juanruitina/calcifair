# -*- coding: utf-8 -*-

import sys
import time
import os.path
from datetime import datetime, timedelta

import board
import busio
import adafruit_sgp30
from ltr559 import LTR559
import ST7789

from PIL import ImageFont
from PIL import ImageDraw
from PIL import Image

# Set up CO2 & VOC sensor
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)

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


def turn_off_display():
    disp.set_backlight(0)


def turn_on_display():
    disp.set_backlight(1)


# Initialize display.
disp.begin()

# Load emoji while starts
image = Image.open('assets/emoji-fire.png')
disp.display(image)

# Calcifer says hi
print("🔥 Calcifer is waking up, please wait...")
# print("SGP30 serial #", [hex(i) for i in sgp30.serial])


def calcifer_expressions(expression):
    if expression == 'talks':
        image = Image.open('assets/calcifer-talks.gif')
    elif expression == 'idle':
        image = Image.open('assets/calcifer-idle.gif')
    elif expression == 'rawr':
        image = Image.open('assets/calcifer-rawr.gif')
    frame = 0
    while frame < image.n_frames:
        try:
            image.seek(frame)
            disp.display(image.resize((WIDTH, HEIGHT)))
            frame += 1
            time.sleep(0.05)
        except EOFError:
            frame = 0


screen_timeout = 0
start_time = datetime.now()

# Initialise air quality sensor
sgp30.iaq_init()

# Load air quality sensor baseline from file
baseline_file = 'sgp30-baseline.txt'
baseline_log = 'logs/sgp30-baseline.txt'
baseline_eCO2_restored, baseline_TVOC_restored = None, None

if os.path.exists(baseline_file):
    baseline_values = {}
    with open(baseline_file, 'r') as file:
        for line in file:
            (key, val) = line.split('=')
            baseline_values[key] = val.rstrip()
        baseline_timestamp = datetime.strptime(
            baseline_values['baseline_timestamp'], '%Y-%m-%d %H:%M:%S')

        # Ignore stored baseline if older than a week
        if datetime.now() < baseline_timestamp + timedelta(days=7):
            baseline_eCO2_restored = int(baseline_values['eco2'], 16)
            baseline_TVOC_restored = int(baseline_values['tvoc'], 16)
            print('Stored baseline is recent enough: 0x{:x} 0x{:x} {}'.format(
                baseline_eCO2_restored, baseline_TVOC_restored, baseline_timestamp))

            # Set baseline
            sgp30.set_iaq_baseline(
                baseline_eCO2_restored, baseline_TVOC_restored)
        else:
            print('Stored baseline is too old')

baseline_log_counter = datetime.now() + timedelta(minutes=10)

# If there are not baseline values stored, wait 12 hours before saving every hour
if baseline_eCO2_restored is None or baseline_TVOC_restored is None:
    baseline_log_counter_valid = datetime.now() + timedelta(hours=12)
    print('Calcifer will store a valid baseline in 12 hours')
else:
    baseline_log_counter_valid = datetime.now() + timedelta(hours=1)

# Wait while sensor warms up
warmup_counter = datetime.now() + timedelta(seconds=30)
while datetime.now() < warmup_counter:
    if sgp30.eCO2 > 400 and sgp30.TVOC > 0:
        break
    time.sleep(1)

while True:
    # Get proximity
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
    # print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

    # Get air quality
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('CO2: {} ppm, VOC: {} ppb | {}'.format(
        sgp30.eCO2, sgp30.TVOC, current_time_str))

    # Log baseline
    if (datetime.now() > baseline_log_counter):
        baseline_log_counter = datetime.now() + timedelta(minutes=10)

        baseline_human = 'CO2: {0} 0x{0:x}, VOC: {1} 0x{1:x} | {2}'.format(
            sgp30.baseline_eCO2, sgp30.baseline_TVOC, current_time_str)

        if (datetime.now() > baseline_log_counter_valid):
            baseline_log_counter_valid = datetime.now() + timedelta(hours=1)
            print("Valid baseline: " + baseline_human)
            with open(baseline_log, 'a') as file:
                file.write("Valid: " + baseline_human + '\n')
            # Store new valid baseline
            with open(baseline_file, 'w') as file:
                file.write('eco2=0x{:x}\ntvoc=0x{:x}\nbaseline_timestamp={}'.format(
                    sgp30.baseline_eCO2, sgp30.baseline_TVOC, current_time_str))
        else:
            print("Baseline: " + baseline_human)
            with open(baseline_log, 'a') as file:
                file.write(baseline_human + '\n')

    # Air quality levels
    # From Hong Kong Indoor Air Quality Management Group
    # https://www.iaq.gov.hk/media/65346/new-iaq-guide_eng.pdf
    air_quality = "good"
    if sgp30.eCO2 > 1000 or sgp30.TVOC > 261:
        air_quality = "bad"
    elif sgp30.eCO2 > 800 or sgp30.TVOC > 87:
        air_quality = "medium"

    # Alerts
    if prox >= 5 or air_quality == "bad" or screen_timeout > 0:
        if prox >= 5:
            screen_timeout = 5  # seconds the screen will stay on
        screen_timeout -= 1

        turn_on_display()

        color = (255, 255, 255)
        background_color = (0, 0, 0)
        if air_quality == "bad":
            background_color = (255, 0, 0)
        elif air_quality == "medium":
            color = (0, 0, 0)
            background_color = (255, 255, 0)

        if background_color != (0, 0, 0):
            img = Image.new('RGB', (WIDTH, HEIGHT), color=background_color)
        else:
            img = Image.open('assets/background.png')

        draw = ImageDraw.Draw(img)

        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
        font_bold = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

        draw.rectangle((0, 0, disp.width, 80), background_color)

        draw.text((10, 10), 'CO2', font=font, fill=color)
        if (sgp30.eCO2 <= 400):
            draw.text((10, 45), '<400', font=font_bold, fill=color)
        else:
            draw.text((10, 45), str(sgp30.eCO2),
                      font=font_bold, fill=color)
        draw.text((10, 80), 'ppm', font=font, fill=color)

        draw.text((125, 10), 'VOC', font=font, fill=color)
        draw.text((125, 45), str(sgp30.TVOC),
                  font=font_bold, fill=color)
        draw.text((125, 80), 'ppb', font=font, fill=color)

        disp.display(img)
    else:
        turn_off_display()

    time.sleep(1.0)
