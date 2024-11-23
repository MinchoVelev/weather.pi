# weather.pi

Raspberry Pi Pico W + an EPD_2in13_V3 e-inc display weather station. 

![preview_image](https://raw.githubusercontent.com/MinchoVelev/weather.pi/refs/heads/main/weatherpi.png)

## How to run

1. Connect the raspberry to Thonny or any other way to manage it.
1. Flash micropython.
2. Replace placeholders
    1. main.py: `<wifi id>`
    2. main.py: `<wifi password>`
    3. lib/weather.py: `<key>` with the key for weatherapi.com
    4. lib/weather.py: `<city>` with the desired city
3. Upload the files to the raspberry
4. Enjoy
