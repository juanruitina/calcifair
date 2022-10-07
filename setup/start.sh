# Remember to make this script executable: chmod +x start.sh
echo 0 | sudo tee /sys/class/leds/led1/brightness
/usr/bin/python3 /home/Calcifer/calcifair/calcifair.py