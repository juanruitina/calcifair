# Calcifer

Calcifer is the [resident fire demon](https://howlscastle.fandom.com/wiki/Calcifer) of a Raspberry Pi located in Madrid, Spain. It captures relevant environmental information from their sensors and shows alerts when things go wrong. Calcifer is written in Python.

## Hardware

For now Calcifer runs on a Raspberry Pi 4 (2GB RAM) with Raspberry, and the following hardware, all bought from [Pimoroni](https://shop.pimoroni.com/):

* SGP-30 Air Quality Sensor Breakout, for equivalent CO2 and volatile organic compounds (TVOC) readings
* 1.3" SPI Colour LCD screen, with a 240×240 resolution.
* LTR-559 Light and Proximity Sensor Breakout, so Calcifer's screen turns on whenever I put my hand close to them

Make sure to install all the drivers from Pimoroni.

## Run Calcifer

``python calcifer.py``

## To do

- [x] Turn off screen when possible
- [ ] Callibrate air quality sensor
- [ ] Show GIF until sensor warms up
- [ ] Check proximity sensor more often than 1s
- [ ] Integrate with https://io.adafruit.com/ or similar
- [ ] Integrate with Home Assistant?