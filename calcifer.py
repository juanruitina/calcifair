import time
import sys

# Set up CO2 & VOC sensor
from sgp30 import SGP30

sgp30 = SGP30()

# result = sgp30.command('set_baseline', (0xFECA, 0xBEBA))
# result = sgp30.command('get_baseline')
# print(["{:02x}".format(n) for n in result])

# Set up light and proximity sensor
from ltr559 import LTR559
ltr559 = LTR559()

# Set up screen
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import ST7789

disp = ST7789.ST7789(
    port=0,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=19,               # 18 for back BG slot, 19 for front BG slot.
    spi_speed_hz=80 * 1000 * 1000
)

WIDTH = disp.width
HEIGHT = disp.height

# Initialize display.
disp.begin()

# Calcifer says hi
image = Image.open('assets/calcifer-rawr-opt.gif')
frame = 0
while frame < image.n_frames:
    try:
        image.seek(frame)
        disp.display(image.resize((WIDTH, HEIGHT)))
        frame += 1
        time.sleep(0.05)
    except EOFError:
        frame = 0
        
print("Sensor warming up, please wait...")

def crude_progress_bar():
    sys.stdout.write('.')
    sys.stdout.flush()

sgp30.start_measurement(crude_progress_bar)
sys.stdout.write('\n')

while True:
    # Get proximity
    ltr559.update_sensor()
    lux = ltr559.get_lux()
    prox = ltr559.get_proximity()
    print("Lux: {:06.2f}, Proximity: {:04d}".format(lux, prox))
        
    # Get air quality
    result = sgp30.get_air_quality()
    print(result)
    
    # Alerts
    color = (255, 255, 255)
    background_color = (0, 0, 0)
    if prox > 5 :
        background_color = (0, 255, 0)
    elif ( result.equivalent_co2 > 1000 ) :
        background_color = (255, 0, 0)
    elif ( result.equivalent_co2 > 700 ) :
        background_color = (255, 165, 0)
    
    img = Image.new('RGB', (WIDTH, HEIGHT), color=background_color )
    draw = ImageDraw.Draw(img)
    
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)

    draw.rectangle((0, 0, disp.width, 80), background_color)
    
    draw.text((10, 10), 'CO2', font=font, fill=color)
    if ( result.equivalent_co2 <= 400 ) :
        draw.text((10, 45), '<400', font=font_bold, fill=color)
    else: 
        draw.text((10, 45), str(result.equivalent_co2), font=font_bold, fill=color)
    draw.text((10, 80), 'ppm', font=font, fill=color)
    
    draw.text((125, 10), 'VOC', font=font, fill=color)
    draw.text((125, 45), str(result.total_voc), font=font_bold, fill=color)
    draw.text((125, 80), 'ppb', font=font, fill=color)
    
    disp.display(img)
     
    time.sleep(1.0)
    
