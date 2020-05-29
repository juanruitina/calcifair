import sys
import time
import os.path

from sgp30 import SGP30
from ltr559 import LTR559
import ST7789

from PIL import ImageFont
from PIL import ImageDraw
from PIL import Image

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

# Calcifer says hi
print("Sensor warming up, please wait...")


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


def crude_progress_bar():
    # calcifer_expressions('talks')
    sys.stdout.write('.')
    sys.stdout.flush()


sgp30.start_measurement(crude_progress_bar)
sys.stdout.write('\n')

while True:
    # Get proximity
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
    # print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))

    # Get air quality
    result = sgp30.get_air_quality()
    print(result)
    print(sgp30.command('get_baseline'))

    # Alerts
    if prox >= 5 or result.equivalent_co2 > 1000:
        turn_on_display()

        color = (255, 255, 255)
        background_color = (0, 0, 0)
        if (result.equivalent_co2 > 1000):
            background_color = (255, 0, 0)
        elif (result.equivalent_co2 > 700):
            background_color = (255, 165, 0)

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
        draw.text((125, 45), str(result.total_voc), font=font_bold, fill=color)
        draw.text((125, 80), 'ppb', font=font, fill=color)

        disp.display(img)
    else:
        turn_off_display()

    time.sleep(1.0)
