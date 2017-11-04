import math
import time

#import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import RPi.GPIO as GPIO

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

# Input pins:
L_pin = 27 
R_pin = 23 
C_pin = 4 
U_pin = 17 
D_pin = 22 
 
A_pin = 5 
B_pin = 6 
 
GPIO.setmode(GPIO.BCM) 
GPIO.setup(A_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(B_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(L_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(R_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(U_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(D_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(C_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up

# Raspberry Pi pin configuration:
RST = 24

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Initialize library.
disp.begin()

# Get display width and height.
width = disp.width
height = disp.height

# Clear display.
disp.clear()
disp.display()

# Create image buffer.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new('1', (width, height))

# Load default font.
font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as this python script!
# Some nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

# Create drawing object.
draw = ImageDraw.Draw(image)

# Set initial parameters
ballx, bally = 0, 0
vx, vy = 1, 1
size = 2

FPS = 30.0
SPF = 1 / FPS
last = time.time()

trace = []
A_pin_down = False

import random
fpscount = 0
fpstimer = time.time()

# Animate
print('Press Ctrl-C to quit.')
while True:
    # Check input
    if GPIO.input(A_pin):
	if A_pin_down:
            vx, vy = random.randint(-10,10), random.randint(-10,10)
            A_pin_down = False
    else:
	A_pin_down = True

    if time.time() - last > SPF:
	last = time.time()

        # Update position
        ballx += vx
        bally += vy
        if ballx < 0:
            ballx = -ballx
            vx = -vx
    	elif ballx >=width-1:
	    ballx = ballx - 2*(ballx-width)
	    vx = -vx
	if bally < 0:
	    bally = -bally
            vy = -vy
        elif bally >= height-1:
            bally = bally - 2*(bally-height)
	    vy = -vy

	trace.append([ballx,bally])
	if len(trace) > 4:
	    trace = trace[1:]

        # Clear image buffer by drawing a black filled box.
        draw.rectangle((0,0,width,height), outline=0, fill=0)
	draw.rectangle((0,0,0,0), outline=0, fill=1)
	draw.rectangle((0,height-1,0,height-1), outline=0, fill=1)
	draw.rectangle((width-1,0,width-1,0), outline=0, fill=1)
	draw.rectangle((width-1,height-1,width-1,height-1), outline=0, fill=1)

        # Draw squares
        draw.rectangle([trace[-1][0]-size,trace[-1][1]-size,trace[-1][0]+size,trace[-1][1]+size], outline=0, fill=1)
        for t in trace[:-1]:
	    draw.rectangle(t+t, outline=0, fill=1)

        # Draw the image buffer.
        disp.image(image)
        disp.display()

	fpscount += 1
	if time.time() - fpstimer > 1:
	    print fpscount
	    fpscount = 0
	    fpstimer = time.time()

    # Pause briefly to get pins up
    time.sleep(0.01)
