#This program was updated from the below original creator.

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
import time
import random
import board
import busio
import signal
from statistics import median as mean
from colorsys import hsv_to_rgb
from digitalio import DigitalInOut, Direction
from PIL import Image, ImageDraw, ImageFont

import adafruit_mlx90640
from adafruit_rgb_display import st7789

udlr_fill = "#00FF00"
udlr_outline = "#00FFFF"
button_fill = "#FF00FF"
button_outline = "#FFFFFF"

fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)

# Input pins
button_A = DigitalInOut(board.D5)
button_A.direction = Direction.INPUT

button_B = DigitalInOut(board.D6)
button_B.direction = Direction.INPUT

button_L = DigitalInOut(board.D27)
button_L.direction = Direction.INPUT

button_R = DigitalInOut(board.D23)
button_R.direction = Direction.INPUT

button_U = DigitalInOut(board.D17)
button_U.direction = Direction.INPUT

button_D = DigitalInOut(board.D22)
button_D.direction = Direction.INPUT

button_C = DigitalInOut(board.D4)
button_C.direction = Direction.INPUT

# Create the display pins
cs_pin = DigitalInOut(board.CE0)
dc_pin = DigitalInOut(board.D25)
reset_pin = DigitalInOut(board.D24)
BAUDRATE = 24000000

#Initialize SPI bus and display.
spi = board.SPI()
disp = st7789.ST7789(
    spi,
    height=240,
    y_offset=80,
    rotation=180,
    cs=cs_pin,
    dc=dc_pin,
    rst=reset_pin,
    baudrate=BAUDRATE,
)

#set constants for temperature range.
MIN_TEMP = 20
MAX_TEMP = 35
SET_TEMP = 0 #0 MIN 1 MAX

#Camera color matrix.
camColorsHex = [0x480F,
0x400F,0x400F,0x400F,0x4010,0x3810,0x3810,0x3810,0x3810,0x3010,0x3010,
0x3010,0x2810,0x2810,0x2810,0x2810,0x2010,0x2010,0x2010,0x1810,0x1810,
0x1811,0x1811,0x1011,0x1011,0x1011,0x0811,0x0811,0x0811,0x0011,0x0011,
0x0011,0x0011,0x0011,0x0031,0x0031,0x0051,0x0072,0x0072,0x0092,0x00B2,
0x00B2,0x00D2,0x00F2,0x00F2,0x0112,0x0132,0x0152,0x0152,0x0172,0x0192,
0x0192,0x01B2,0x01D2,0x01F3,0x01F3,0x0213,0x0233,0x0253,0x0253,0x0273,
0x0293,0x02B3,0x02D3,0x02D3,0x02F3,0x0313,0x0333,0x0333,0x0353,0x0373,
0x0394,0x03B4,0x03D4,0x03D4,0x03F4,0x0414,0x0434,0x0454,0x0474,0x0474,
0x0494,0x04B4,0x04D4,0x04F4,0x0514,0x0534,0x0534,0x0554,0x0554,0x0574,
0x0574,0x0573,0x0573,0x0573,0x0572,0x0572,0x0572,0x0571,0x0591,0x0591,
0x0590,0x0590,0x058F,0x058F,0x058F,0x058E,0x05AE,0x05AE,0x05AD,0x05AD,
0x05AD,0x05AC,0x05AC,0x05AB,0x05CB,0x05CB,0x05CA,0x05CA,0x05CA,0x05C9,
0x05C9,0x05C8,0x05E8,0x05E8,0x05E7,0x05E7,0x05E6,0x05E6,0x05E6,0x05E5,
0x05E5,0x0604,0x0604,0x0604,0x0603,0x0603,0x0602,0x0602,0x0601,0x0621,
0x0621,0x0620,0x0620,0x0620,0x0620,0x0E20,0x0E20,0x0E40,0x1640,0x1640,
0x1E40,0x1E40,0x2640,0x2640,0x2E40,0x2E60,0x3660,0x3660,0x3E60,0x3E60,
0x3E60,0x4660,0x4660,0x4E60,0x4E80,0x5680,0x5680,0x5E80,0x5E80,0x6680,
0x6680,0x6E80,0x6EA0,0x76A0,0x76A0,0x7EA0,0x7EA0,0x86A0,0x86A0,0x8EA0,
0x8EC0,0x96C0,0x96C0,0x9EC0,0x9EC0,0xA6C0,0xAEC0,0xAEC0,0xB6E0,0xB6E0,
0xBEE0,0xBEE0,0xC6E0,0xC6E0,0xCEE0,0xCEE0,0xD6E0,0xD700,0xDF00,0xDEE0,
0xDEC0,0xDEA0,0xDE80,0xDE80,0xE660,0xE640,0xE620,0xE600,0xE5E0,0xE5C0,
0xE5A0,0xE580,0xE560,0xE540,0xE520,0xE500,0xE4E0,0xE4C0,0xE4A0,0xE480,
0xE460,0xEC40,0xEC20,0xEC00,0xEBE0,0xEBC0,0xEBA0,0xEB80,0xEB60,0xEB40,
0xEB20,0xEB00,0xEAE0,0xEAC0,0xEAA0,0xEA80,0xEA60,0xEA40,0xF220,0xF200,
0xF1E0,0xF1C0,0xF1A0,0xF180,0xF160,0xF140,0xF100,0xF0E0,0xF0C0,0xF0A0,
0xF080,0xF060,0xF040,0xF020,0xF800]

camColors = [[]]

#Convert pixel from RGB 565 format into RGB 888
def ConvertRGB565toRGB888(pixelColor):
    red = (pixelColor & 0xF800) >> 11
    green = (pixelColor & 0x07E0) >> 5
    blue = pixelColor & 0x001F
    return (red,green,blue)

#Map the temperature to an index in the color matrix
def colorMap(value,minVal,maxVal):
    return ((value - minVal) * (255)) / (maxVal - minVal)

#Convert color space
def TransformColorSpace(startArray):
    for i in range(len(startArray)-1):
        camColors.append(ConvertRGB565toRGB888(camColorsHex[i]))

#Get temperature from camera and print a text representation of the acquire array
def getTemp(listVal = False):
    try:
        mlx.getFrame(frame)
    except ValueError:
        # these happen, no biggie - retry
        return 0
    if (listVal):
        print("Read 2 frames in %0.2f s" % (time.monotonic() - stamp))
        for h in range(24):
            for w in range(32):
                t = frame[h * 32 + w]
                if PRINT_TEMPERATURES:
                    print("%0.1f, " % t, end="")
                if PRINT_ASCIIART:
                    c = "&"
                    # pylint: disable=multiple-statements
                    if t < 20:
                        c = " "
                    elif t < 23:
                        c = "."
                    elif t < 25:
                        c = "-"
                    elif t < 27:
                        c = "*"
                    elif t < 29:
                        c = "+"
                    elif t < 31:
                        c = "x"
                    elif t < 33:
                        c = "%"
                    elif t < 35:
                        c = "#"
                    elif t < 37:
                        c = "X"
                    # pylint: enable=multiple-statements
                    print(c, end="")
            print()
        print()

#Display temperature statistics on I2C display
def displayStats(vMin = 0,vMax = 100,vAvg = 50):
    txtMinData = "Min "+'{:.{prec}f}'.format(vMin, prec=2) 
    txtMaxData =  "Max " + '{:.{prec}f}'.format(vMax, prec=2) 
    txtAvgData = "Avg "+'{:.{prec}f}'.format(vAvg, prec=2)
    txtOneLine = '{:.{prec}f},'.format(vMin, prec=1)+'{:.{prec}f},'.format(vMax, prec=1)+'{:.{prec}f}'.format(vAvg, prec=1)
    
    draw.text((20, 200), txtOneLine, font=fnt, fill=rcolor)

#Check for any keys pressed, and adjust the temperature according.
def processKeys():
    global MAX_TEMP, MIN_TEMP
    if not button_U.value:  # up pressed
        MAX_TEMP = MAX_TEMP+1
        print(MAX_TEMP)

    if not button_D.value:  # down pressed
        MAX_TEMP = MAX_TEMP-1
        print(MAX_TEMP)

    if not button_L.value:  # left pressed
        MIN_TEMP=MIN_TEMP-1
        print(MIN_TEMP)

    if not button_R.value:  # right pressed
        MIN_TEMP=MIN_TEMP+1
        print(MIN_TEMP)

    #if not button_C.value:  # center pressed

    if not button_A.value:  # left pressed
        MIN_TEMP=-5
        MAX_TEMP=20
        print('A')

    if not button_B.value:  # left pressed
        MIN_TEMP=20
        MAX_TEMP=38
        print('B')

#Refresh the thermo data and stats.
def refreshTemp():
    global MAX_TEMP, MIN_TEMP, rcolor, fnt

    offset = 7
    pos = 240; #offset_canvas.width
    draw.rectangle((20, 170, 240, 240), fill=0)  # center
    my_text = str(MIN_TEMP)+" - "+str(MAX_TEMP)
    draw.text((20, 170), my_text, font=fnt, fill=rcolor)
    getTemp()
    
    maxTemp=max(frame)
    minTemp=min(frame)
    avgTemp=mean(frame)
    for h in range(24):
        for w in range(32):
            t = frame[h * 32 + w]
            if (t < MIN_TEMP or t > MAX_TEMP):
                color = 0 
            else:
                t = min(t,MAX_TEMP)
                t = max(t,MIN_TEMP)
                colorIdx = int(colorMap(t,MIN_TEMP,MAX_TEMP))
                if (colorIdx < CL):
                    color = camColorsHex[colorIdx]
                else:
                    color = 0 
            draw.rectangle((w*offset,h*offset,(w*offset+(offset-1)),(h*offset+(offset-1))), fill=color)

    displayStats(minTemp,maxTemp,avgTemp)   
    # Display the Image
    disp.image(image)

# Turn on the Backlight
backlight = DigitalInOut(board.D26)
backlight.switch_to_output()
backlight.value = True

# Create blank image for drawing.
# Make sure to create image with mode 'RGB' for color.
width = disp.width
height = disp.height
image = Image.new("RGB", (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Clear display.
draw.rectangle((0, 0, width, height), outline=0, fill=(255, 0, 0))
disp.image(image)

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0, 0, width, height), outline=0, fill=0)

#Initialize color matrix
TransformColorSpace(camColorsHex)

PRINT_TEMPERATURES = True
PRINT_ASCIIART = False

#Thermal camera buffer
frame = [0] * 768

#Initialize RPi I2C bus.
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000) 

#init values
WIDTH = 128
HEIGHT = 64  # Change to 64 if needed
BORDER = 5

#Initialize thermal camera
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])
#set refresh rate
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ

# make a random color and print text
rcolor = "#00FFFF"

# Main function
if __name__ == "__main__":
    CL = len(camColors)
    getTemp()

    while True:
        processKeys()
        refreshTemp()
