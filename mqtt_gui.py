import math
import time

'''
OLED STUFF
'''

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
RST = None

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
#font = ImageFont.truetype('slkscr.ttf', 8)

# Create drawing object.
draw = ImageDraw.Draw(image)

'''
WINDOW MANAGEMENT
'''

class Window:
	def __init__(self, x, y, width, height):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.subwindows = None
		self.subwins_vertical = None
		self.content = None

	def create_subwindows(self, border_arr, vertical=True):
		if self.content is not None:
			raise ValueError("Warning: You are creating subwindows but already have content!")
		if vertical:
			if max(border_arr) >= self.width-1:
				raise ValueError("Cannot create subwindows outside of current Window!")
			self.subwins_vertical = True
			last = self.y
			self.subwindows = []
			for step in border_arr + [self.height]:
				self.subwindows.apped(Window(self.x, last, self.x+self.width, self.y+step))
				last = step
		else:
			if max(border_arr) >= self.height-1:
				raise ValueError("Cannot create subwindows outside of current Window!")
			self.subwins_vertical = False
			last = self.x
			self.subwindows = []
			for step in border_arr + [self.width]:
				self.subwindows.apped(Window(last, self.y, self.x+step, self.y+self.height))
				last = step

	def add_content(self, content):
		if self.subwindows is not None:
			raise ValueError("Warning: You are adding content but already have subwindows!")
		self.content = content

	def draw(self):
		if self.content is None and self.subwindows is None:
			draw.rectangle((self.x,self.y,self.width,self.height), outline=0, fill=1)
		elif self.subwindows is not None:
			for subwin in self.subwindows:
				subwin.draw()
		else:
			self.content.draw()

# Create root Window
rootwin = Window(0, 0, 128, 64)

# Clear initially
rootwin.draw()
disp.image(image)
disp.display()

'''
CALLBACKS
'''

def show_message(msg):
	# Check input
	if GPIO.input(A_pin):
		pass
	else:
		pass

	# Clear image buffer by drawing a white filled box.
	draw.rectangle((0,0,width,height), outline=0, fill=0)

	# Draw message
	for item in msg:
		draw.text(item[0], item[1], font=font, fill=1)

	# Draw the image buffer.
	disp.image(image)
	disp.display()

'''
MQTT STUFF
'''

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	show_message([[(0,0), "Connected: " + str(rc)]])

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
#	client.subscribe("$SYS/#")
	client.subscribe("wits/project/coffee/coffee1")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	try:
		mess = []
		for i in range(0, (len(msg.topic)//20)+1):
			mess.append( [(0,i*10), msg.topic[i*20:i*20+20]] )
		pad = len(mess)
		for j in range(0, (len(msg.payload)//20)+1):
			mess.append( [(0,(pad+j)*10), msg.payload[j*20:j*20+20]] )
		show_message(mess)
	except UnicodeDecodeError:
		show_message([ [(0,0),"Error"] ])

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.hivemq.com", 1883, 8000)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
