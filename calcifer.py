# -*- coding: utf-8 -*-

from functools import wraps
import sys
import time
import os.path
from datetime import datetime, timedelta
import yaml

from sgp30 import SGP30

from ltr559 import LTR559
import ST7789

from PIL import ImageFont, ImageDraw, Image

import logging
from telegram.ext import Updater, CommandHandler, Filters

# Load configuration file
config = None
with open('config.yaml') as file:
    config = yaml.full_load(file)

logging.basicConfig(filename='logs/python.txt')

# Set up CO2 & VOC sensor
sgp30 = SGP30()

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

# Initialize Telegram
updater = Updater(
    token=config['telegram']['token'], use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Restrict to certain Telegram users
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Code-snippets#restrict-access-to-a-handler-decorator


def restricted(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        global config
        user_id = update.effective_user.id
        if user_id not in config['telegram']['authorized_user_ids']:
            print("Unauthorized access denied for {}".format(user_id))
            return
        return func(update, context, *args, **kwargs)
    return wrapped


@restricted
def start(update, context):
    tg_message = ""
    if sgp30.air_quality:
        if sgp30.air_quality == 'bad':
            tg_message += "\nHuele a tigre. Haz el favor de ventilar. 🔥"
        if sgp30.air_quality == 'medium':
            tg_message += "\nEl ambiente está un poco cargado. No nos vendría mal ventilar 🏡"
        if sgp30.air_quality == 'good':
            tg_message += "\nQué aire más limpio 💖"
        tg_message += "\nCO2: {} ppm, VOC: {} ppb".format(
            result.equivalent_co2, result.total_voc)
    else:
        tg_message += "\nTodavía estoy poniéndome en marcha, así que no tengo datos aún"

    context.bot.send_message(
        chat_id=update.effective_chat.id, text=tg_message)


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)
updater.start_polling()

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

# Air quality levels
# From Hong Kong Indoor Air Quality Management Group
# https://www.iaq.gov.hk/media/65346/new-iaq-guide_eng.pdf


def air_quality():
    global sgp30
    if sgp30:
        if result.equivalent_co2 and result.total_voc:
            if result.equivalent_co2 > 1000 or result.total_voc > 261:
                sgp30.air_quality = "bad"
            elif result.equivalent_co2 > 800 or result.total_voc > 87:
                sgp30.air_quality = "medium"
            else:
                sgp30.air_quality = "good"
        else:
            sgp30.air_quality = "unknown"


screen_timeout = 0
start_time = datetime.now()

# Initialise air quality sensor


def crude_progress_bar():
    # calcifer_expressions('talks')
    sys.stdout.write('.')
    sys.stdout.flush()


sgp30.start_measurement(crude_progress_bar)
sys.stdout.write('\n')

# Load air quality sensor baseline from config file
baseline_eCO2_restored, baseline_TVOC_restored, baseline_timestamp = None, None, None
if config['sgp30_baseline']['timestamp'] is not None:
    baseline_timestamp = config['sgp30_baseline']['timestamp']

    # Ignore stored baseline if older than a week
    if datetime.now() < baseline_timestamp + timedelta(days=7):
        baseline_eCO2_restored = config['sgp30_baseline']['eCO2']
        baseline_TVOC_restored = config['sgp30_baseline']['TVOC']

        print('Stored baseline is recent enough: 0x{:x} 0x{:x} {}'.format(
            baseline_eCO2_restored, baseline_TVOC_restored, baseline_timestamp))

        # Set baseline
        result = sgp30.command(
            'set_baseline', (baseline_eCO2_restored, baseline_TVOC_restored))
    else:
        print('Stored baseline is too old')

baseline_log = 'logs/sgp30-baseline.txt'
baseline_log_counter = datetime.now() + timedelta(minutes=10)

# If there are not baseline values stored, wait 12 hours before saving every hour
if baseline_eCO2_restored is None or baseline_TVOC_restored is None:
    baseline_log_counter_valid = datetime.now() + timedelta(hours=12)
    print('Calcifer will store a valid baseline in 12 hours')
else:
    baseline_log_counter_valid = datetime.now() + timedelta(hours=1)


while True:
    result = sgp30.get_air_quality()
    air_quality()

    # Get proximity
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
    # print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

    # Get air quality
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('CO2: {} ppm, VOC: {} ppb | {}'.format(
        result.equivalent_co2, result.total_voc, current_time_str))

    # Log baseline
    baseline_get = sgp30.command('get_baseline')
    baseline_human = 'CO2: {0} 0x{0:x}, VOC: {1} 0x{1:x} | {2}'.format(
        baseline_get[0], baseline_get[1], current_time_str)

    if datetime.now() > baseline_log_counter_valid:
        baseline_log_counter_valid = datetime.now() + timedelta(hours=1)
        print("Valid baseline: " + baseline_human)
        with open(baseline_log, 'a') as file:
            file.write("Valid: " + baseline_human + '\n')

        # Store new valid baseline
        config['sgp30_baseline']['eCO2'] = baseline_get[0]
        config['sgp30_baseline']['TVOC'] = baseline_get[1]
        config['sgp30_baseline']['timestamp'] = datetime.now()

        with open('config.yaml', 'w') as file:
            yaml.dump(config, file)
            print('Baseline updated on config file')

    elif datetime.now() > baseline_log_counter:
        baseline_log_counter = datetime.now() + timedelta(minutes=10)

        print("Baseline: " + baseline_human)
        with open(baseline_log, 'a') as file:
            file.write(baseline_human + '\n')

    # Alerts
    if prox >= 5 or screen_timeout > 0:
        if prox >= 5:
            screen_timeout = 5  # seconds the screen will stay on
        screen_timeout -= 1

        turn_on_display()

        color = (255, 255, 255)
        background_color = (0, 0, 0)
        if sgp30.air_quality == "bad":
            background_color = (255, 0, 0)
        elif sgp30.air_quality == "medium":
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
        if (result.equivalent_co2 <= 400):
            draw.text((10, 45), '<400', font=font_bold, fill=color)
        else:
            draw.text((10, 45), str(result.equivalent_co2),
                      font=font_bold, fill=color)
        draw.text((10, 80), 'ppm', font=font, fill=color)

        draw.text((125, 10), 'VOC', font=font, fill=color)
        draw.text((125, 45), str(result.total_voc),
                  font=font_bold, fill=color)
        draw.text((125, 80), 'ppb', font=font, fill=color)

        disp.display(img)
    else:
        turn_off_display()

    time.sleep(1.0)
