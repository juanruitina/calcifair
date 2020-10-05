# 🔥 Calcifair

Calcifair is the [resident fire demon](https://howlscastle.fandom.com/wiki/Calcifer) of a Raspberry Pi located in Madrid, Spain. It currently gives information and shows alerts about air quality. Calcifer is written in Python 3.

* Gather indoors air quality levels via the SGP-30 sensor and get outdoors air quality from the IQAir AirVisual API.
* Receive air quality information by asking a Telegram bot.

## Hardware

For now Calcifair runs on a Raspberry Pi 4 (2GB RAM) with Raspbian, and the following hardware, all bought from [Pimoroni](https://shop.pimoroni.com/):

- **SGP-30 Air Quality Sensor Breakout**, for equivalent CO2 and volatile organic compounds (TVOC) reading ([using library from Adafruit](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test)).
- **ST7789 1.3" SPI Colour LCD screen**, with 240×240 resolution.
- **LTR-559 Light and Proximity Sensor Breakout**, so Calcifer's screen turns on whenever I put my hand close to them.
- **Breakout Garden** (I2C + SPI).

Unless otherwise stated, make sure to install the libraries from Pimoroni.

## Run Calcifair

Before running for the first time, copy `config-sample.yaml`, rename as `config.yaml` and include your Telegram bot and IQAir AirVisual API tokens and the IDs of the authorised Telegram users.

`python3 calcifair.py`

## To do

- [x] Turn off screen when possible
- [x] Calibrate air quality sensor with baseline
- [x] Integrate with Telegram bot
- [x] Integrate with https://io.adafruit.com/ or similar
- [ ] Get alerts on Telegram
- [ ] Calibrate air quality sensor with humidity
- [ ] Check that images exist (and their format)
- [ ] Add web server for live results (Flask?)
- [ ] Show GIF while sensor warms up
- [ ] Integrate with Home Assistant?

## Licences

- My installation makes use of images and animated GIFs of Calcifer, from the "Howl's Moving Castle" feature film by Studio Ghibli. I downloaded them from Giphy, Tenor, or elsewhere. Since they are probably copyrighted, I have removed them from the repo.
  - Whichever image you use, make sure it's squared.
  - Have a look at the `calcifer_expressions()` function and rewrite it as needed to avoid errors.
- Emojis are from [Twemoji](https://twemoji.twitter.com/), licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Dependencies

```sh
pip3 install adafruit-blinka
pip3 install adafruit-io
pip3 install adafruit-circuitpython-lis3dh
pip3 install adafruit-circuitpython-sgp30
pip3 install ltr559

sudo apt-get update
sudo apt-get install python-rpi.gpio python-spidev python-pip python-pil python-numpy
pip3 install st7789

pip3 install python-telegram-bot
pip3 install PyYAML
pip3 install setproctitle
```