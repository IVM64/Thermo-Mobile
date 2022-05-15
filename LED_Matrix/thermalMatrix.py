#This program was updated from the below original creator.

# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
from typing import NoReturn
import board
import busio
import adafruit_mlx90640
from samplebase import SampleBase
from rgbmatrix import graphics
import touchphat
import signal
import digitalio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
from statistics import median as mean

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

#class to refresh the pixel array device
class SimpleSquare(SampleBase):
    #initialize settings
    def __init__(self, *args, **kwargs):
        super(SimpleSquare, self).__init__(*args, **kwargs)
        self.parser.add_argument("-t", "--text", help="The text to scroll on the RGB LED panel", default="Hello world!")

    #Task to run
    def run(self):
        offset_canvas = self.matrix.CreateFrameCanvas()
        font = graphics.Font()
        font.LoadFont("../rpi-rgb-led-matrix/fonts/7x13.bdf")
        textColor = graphics.Color(255, 255, 0)
        pos = offset_canvas.width
        while True:
            #format range text to display
            my_text = str(MIN_TEMP)+" - "+str(MAX_TEMP)
            #get temperature
            getTemp()
            maxTemp=max(frame)
            minTemp=min(frame)
            avgTemp=mean(frame)
            #run thru the thermal camera data and update each pixel
            for h in range(24):
                for w in range(32):
                    t = frame[h * 32 + w]
                    if (t < MIN_TEMP or t > MAX_TEMP):
                        color = [0,0,0]
                    else:
                        t = min(t,MAX_TEMP)
                        t = max(t,MIN_TEMP)
                        #map the temperature with the color matrix
                        colorIdx = int(colorMap(t,MIN_TEMP,MAX_TEMP))
                        if (colorIdx < CL):
                            color = camColors[colorIdx]
                        else:
                            color = [0,0,0]
                    if (len(color) < 3):
                        color = [0,0,0]
                    offset_canvas.SetPixel(w*2,h*2,color[0],color[1],color[2])
                    offset_canvas.SetPixel((w*2+1),h*2,color[0],color[1],color[2])
                    offset_canvas.SetPixel(w*2,(h*2+1),color[0],color[1],color[2])
                    offset_canvas.SetPixel((w*2+1),(h*2+1),color[0],color[1],color[2])

            #Clear the text area
            for h in range(16):
                for w in range(64):
                    offset_canvas.SetPixel(w,(h+48),0,0,0)
            #Draw the range text
            graphics.DrawText(offset_canvas, font, 0, 60, textColor, my_text)

            offset_canvas = self.matrix.SwapOnVSync(offset_canvas)
            #Display stats on external I2C monitor
            displayStats(minTemp,maxTemp,avgTemp)

#Convert color space
def TransformColorSpace(startArray):
    for i in range(len(startArray)-1):
        camColors.append(ConvertRGB565toRGB888(camColorsHex[i]))

#Get temperature from camera and print a text representation of the acquire array
def getTemp(listVal = False):
    stamp = time.monotonic()
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
                    print(c, end="")
            print()
        print()

#Enable Pimoroni touch hat.
@touchphat.on_touch(['Back','A','B','C','D','Enter'])
#Handle touch events.
def handle_touch(event):
    global MIN_TEMP,MAX_TEMP, SET_TEMP
    print(event.name)
    #set temperature range depending on key pressed
    if (event.name == 'A'):
        MIN_TEMP=-5
        MAX_TEMP=20
    elif (event.name == 'B'):
        MIN_TEMP=20
        MAX_TEMP=38
    elif (event.name == 'C'):
        SET_TEMP = 1
    elif (event.name == 'D'):
        SET_TEMP = 0
    elif (event.name == 'Enter'):
        if (SET_TEMP == 0):
            MIN_TEMP=MIN_TEMP+1
        else:
            MAX_TEMP = MAX_TEMP+1
    elif (event.name == 'Back'):
        if (SET_TEMP == 0):
            MIN_TEMP=MIN_TEMP-1
        else:
            MAX_TEMP = MAX_TEMP-1

#Display temperature statistics on I2C display
def displayStats(vMin = 0,vMax = 100,vAvg = 50):
    txtMinData = "Min "+'{:.{prec}f}'.format(vMin, prec=2) 
    txtMaxData =  "Max " + '{:.{prec}f}'.format(vMax, prec=2) 
    txtAvgData = "Avg "+'{:.{prec}f}'.format(vAvg, prec=2)
    oled.fill(0)
    oled.show()
    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    image = Image.new("1", (oled.width, oled.height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a white background
    draw.rectangle((0, 0, oled.width, oled.height), outline=255, fill=255)

    # Draw a smaller inner rectangle
    draw.rectangle(
        (BORDER, BORDER, oled.width - BORDER - 1, oled.height - BORDER - 1),
        outline=0,
        fill=0,
    )

    # Load default font.
    font = ImageFont.load_default()

    # Draw Some Text
    text = "Hello World!"
    (font_width, font_height) = font.getsize(txtMinData)
    draw.text(
        (oled.width // 2 - font_width // 2, 5),
        txtMinData,
        font=font,
        fill=255,
    )

    (font_width, font_height) = font.getsize(txtMaxData)
    draw.text(
        (oled.width // 2 - font_width // 2, 1*(oled.height // 3 - font_height // 3)),
        txtMaxData,
        font=font,
        fill=255,
    )

    (font_width, font_height) = font.getsize(txtAvgData)
    draw.text(
        (oled.width // 2 - font_width // 2, 2*(oled.height // 3 - font_height // 3)),
        txtAvgData,
        font=font,
        fill=255,
    )

    # Display image
    oled.image(image)
    oled.show()

#Initialize color matrix
TransformColorSpace(camColorsHex)

PRINT_TEMPERATURES = True
PRINT_ASCIIART = False

#Thermal camera buffer
frame = [0] * 768

#Initialize RPi I2C bus.
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)

#init values
WIDTH = 128
HEIGHT = 64  
BORDER = 5

# Define the Reset Pin
oled_reset = digitalio.DigitalInOut(board.D4)
#Initialize oled device
oled = adafruit_ssd1306.SSD1306_I2C(WIDTH, HEIGHT, i2c, addr=0x3D, reset=oled_reset)
#Initialize thermal camera
mlx = adafruit_mlx90640.MLX90640(i2c)
print("MLX addr detected on I2C")
print([hex(i) for i in mlx.serial_number])
#set refresh rate
mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ

# Main function
if __name__ == "__main__":
    #Test leds on touch hat
    for pad in ['Back','A','B','C','D','Enter']:
        touchphat.set_led(pad, True)
        time.sleep(0.1)
        touchphat.set_led(pad, False)
        time.sleep(0.1)

    #Init first round of data
    CL = len(camColors)
    displayStats()
    getTemp()

    #Start task.
    simple_square = SimpleSquare()
    if (not simple_square.process()):
        simple_square.print_help()
