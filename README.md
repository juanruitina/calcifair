# 🔥 Calcifair

Calcifair is the [resident fire demon](https://howlscastle.fandom.com/wiki/Calcifer) of a Raspberry Pi located in Madrid, Spain. It currently gives information and shows alerts about environmental parameters, such as air quality. Calcifair is written in Python 3.

* Gather indoor air quality levels via the SGP-30 sensor and temperature and humidity via the BME280 sensor.
* Get outdoor temperature, humidity and air quality info from the IQAir AirVisual API.
* Receive air quality information by asking a Telegram bot.

## Hardware

For now Calcifair runs on a Raspberry Pi 4 (2GB RAM) with Raspbian, and the following hardware bought from [Pimoroni](https://shop.pimoroni.com/):

- **SGP-30 Air Quality Sensor Breakout**, for equivalent CO2 and volatile organic compounds (TVOC) reading ([using library from Adafruit](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test)).
- **BME280 Temperature, Pressure and Humidity Sensor Breakout** ([using library from Adafruit](https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout/python-circuitpython-test)).
- **ST7789 1.3" SPI Colour LCD screen**, with 240×240 resolution.
- **LTR-559 Light and Proximity Sensor Breakout**, so Calcifer's screen turns on whenever I put my hand close to them.
- **Breakout Garden** (I2C + SPI).
- Little GPIO fan bought from [AliExpress](https://es.aliexpress.com/item/4000302941860.html) for cooling up Calcifair and improving temperature readings.

## Install

Dependencies are managed by [`pipenv`](https://pipenv-es.readthedocs.io/es/latest/index.html).

```sh
sudo apt-get update
sudo apt-get install python-pip libatlas-base-dev
pip3 install pipenv
pipenv install
```

## Run Calcifair

Before running for the first time, copy `config-sample.yaml`, rename as `config.yaml` and include your [Telegram bot](https://www.youtube.com/watch?v=IP2cP6uvTxA) and [IQAir AirVisual API](https://api-docs.iqair.com/) tokens and the IDs of the authorised Telegram users.

`python3 calcifair.py`

Or:

`pipenv run python3 calcifair.py`

## Callibration

Calcifair automatically handles the callibration of the SGP-30 sensor by storing and setting baselines following [these considerations](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test#baseline-set-and-get-2980177-19).

Readings seem to have pretty disparate levels of accuracy. eCO2 readings seem reasonable. When compared with other sensors I have around, temperature readings seem accurate (but a fan might be needed), and humidity readings seem like 10 points higher. The TVOC readings, well, they stay in moderately high levels even after proper ventilation. They might be accurate (I can't compare with other sensors), but I have deliberatly chosen not to believe them for the sake of my own sanity.

## Licences

- My installation makes use of images and animated GIFs of Calcifer, from the "Howl's Moving Castle" feature film by Studio Ghibli. I downloaded them from Giphy, Tenor, or elsewhere. Since they are probably copyrighted, I have removed them from the repo.
  - Whichever image you use, make sure it's squared.
  - Have a look at the `calcifer_expressions()` function and rewrite it as needed to avoid errors.
- Emojis are from [Twemoji](https://twemoji.twitter.com/), licensed under [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## To do/Ideas

- [x] Turn off screen when possible
- [x] Calibrate air quality sensor with baseline
- [x] Integrate with Telegram bot
- [x] Integrate with https://io.adafruit.com/ or similar
- [x] Get alerts on Telegram
- [ ] Calibrate air quality sensor with humidity
- [ ] Check that images exist (and their format)
- [ ] Add web server for live results (Flask?)
- [ ] Show GIF while sensor warms up
- [ ] Integrate with Home Assistant?