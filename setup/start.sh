# Remember to make this script executable: chmod +x start.sh
echo 0 | sudo tee /sys/class/leds/led1/brightness
cd /home/pi/calcifair && sleep 5 && /usr/bin/python3 calcifair.py