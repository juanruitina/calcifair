# 🔥 Calcifair

Calcifair is the [resident fire demon](https://howlscastle.fandom.com/wiki/Calcifer) of a Raspberry Pi located in Madrid, Spain. It currently gives information and shows alerts about environmental parameters, such as air quality. Calcifair is written in Python 3.

* Gather indoor air quality levels via the SGP-30 sensor and temperature and humidity via the BME280 sensor.
* Get outdoor temperature, humidity and air quality info from the IQAir AirVisual API.
* Provide air quality information by asking a Telegram bot.
* Publish air quality information via MQTT so it can be picked up by Home Assistant.

## Hardware

For now Calcifair runs on a Raspberry Pi 4 (2GB RAM) with Raspberry Pi OS 10 (bullseye), and the following hardware bought from [Pimoroni](https://shop.pimoroni.com/):

- **SGP-30 Air Quality Sensor Breakout**, for equivalent CO2 and volatile organic compounds (TVOC) reading ([using library from Adafruit](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test)).
- **BME280 Temperature, Pressure and Humidity Sensor Breakout** ([using library from Adafruit](https://learn.adafruit.com/adafruit-bme280-humidity-barometric-pressure-temperature-sensor-breakout/python-circuitpython-test)).
- **ST7789 1.3" SPI Colour LCD screen**, with 240×240 resolution.
- **LTR-559 Light and Proximity Sensor Breakout**, so Calcifer's screen turns on whenever I put my hand close to them.
- **Breakout Garden** (I2C + SPI).
- Little GPIO fan bought from [AliExpress](https://es.aliexpress.com/item/4000302941860.html) for cooling up Calcifair and improving temperature readings (currently not in use).

## Install

```sh
sudo apt update
sudo apt install python-pip libatlas-base-dev
pip install adafruit-circuitpython-sgp30 adafruit-circuitpython-bme280 adafruit-io ltr559 numpy pillow python-telegram-bot pyyaml "rpi.gpio" setproctitle smbus smbus2 spidev st7789 psutil python-dateutil paho-mqtt get-mac --upgrade
```

## Run Calcifair

Before running for the first time, copy `config-sample.yaml`, rename as `config.yaml` and include your [Telegram bot](https://www.youtube.com/watch?v=IP2cP6uvTxA) and [IQAir AirVisual API](https://api-docs.iqair.com/) tokens and the IDs of the authorised Telegram users.

`python3 calcifair.py`

Or:

`/usr/bin/python3 calcifair.py`

## Set up terminal commands

Add the following lines to `~/.bashrc` (for instance using `sudo nano ~/.bashrc`):

```sh
alias calcifair-run='python3 ~/calcifair/calcifair.py'
alias calcifair-kill='pkill calcifair-main'
alias calcifair-restart='calcifair-kill && calcifair-run'
```

Then run `calcifair-run` to start Calcifair and `calcifair-kill` to stop it.

## Run on boot

Make `setup/start.sh` executable: `chmod +x setup/start.sh`

Then add the following lines to `crontab` (add them using `crontab -e`):

```sh
@reboot sleep 30 && /home/Calcifer/calcifair/setup/start.sh
```

## Callibration

Calcifair automatically handles the callibration of the SGP-30 sensor by storing and setting baselines following [these considerations](https://learn.adafruit.com/adafruit-sgp30-gas-tvoc-eco2-mox-sensor/circuitpython-wiring-test#baseline-set-and-get-2980177-19).

Readings seem to have pretty disparate levels of accuracy. eCO2 readings seem reasonable. When compared with other sensors I have around, temperature readings seem accurate (but a fan might be needed), and humidity readings seem like 10 points higher. The TVOC readings, well, they stay in moderately high levels even after proper ventilation. They might be accurate (I can't compare with other sensors), but I have deliberatly chosen not to believe them for the sake of my own sanity.

## Setting air quality levels

The SGP-30 Air Quality Sensor Breakout measures equivalent carbon dioxyde (eCO2) in parts per million (ppm) and total volatile organic compounds (TVOC) in parts per billion (ppb). There are many different air quality standards set by a variety of agencies all around the world. I have so far relied on those set by the [Hong Kong Indoor Air Quality Management Group](https://www.iaq.gov.hk/media/65346/new-iaq-guide_eng.pdf), as they are the only ones I could find that provided levels in those units.

### Volatile organic compounds

Air quality standards for total VOC are usually set in μg/m3, but the SGP-30 sensor measures in parts per billion (ppb).

However, [according to the manufacturer Sensirion](https://www.catsensors.com/media/pdf/Sensor_Sensirion_IAM.pdf), "The ppb-TVOC output of SGP30 is tuned for the gas mixture utilized by Mølhave et al. featuring a composition of 22 VOCs at concentrations similar to those determined on average in residential indoor environments. The mean molar mass of this mixture is 110 g/mol and hence, 1 ppb TVOC corresponds to 4.5 μg/m3."

So if you would rather use a different standard set in μg/m3, just make sure to divide the TVOC levels in ppb by 4.5.

### Other pollutants

Although the SGP-30 sensor only measures CO2 and TVOC, you can use these two indicators as proxies for overall air quality.

In particular, CO2 monitors have been used during the COVID-19 pandemic to identify poorly ventilated areas, where there could be higher concentrations of aerosols and an increased risk of contagion. There is also evidence that [CO2 readings can be used as a proxy for particulate matter levels (PM2.5, PM10)](https://www.sciencedirect.com/science/article/abs/pii/S0360132315001274).

If levels of either CO2 or TVOC are too high, consider ventilating. Also be mindful of activities that are particularly polluting, such as cooking and cleaning.

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
- [x] Integrate with Home Assistant
- [ ] Calibrate air quality sensor with humidity
- [ ] Check that images exist (and their format)
- [ ] Show GIF while sensor warms up

## Notes

- To update `requirements.txt`: `pip freeze > requirements.txt`