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
			if max(border_arr) >= self.height-1:
				raise ValueError("Cannot create subwindows outside of current Window!")
			self.subwins_vertical = True
			last = 0
			self.subwindows = []
			for step in border_arr + [self.height]:
				self.subwindows.append(Window(self.x, self.y+last, self.width, step-last))
				last = step
		else:
			if max(border_arr) >= self.width-1:
				raise ValueError("Cannot create subwindows outside of current Window!")
			self.subwins_vertical = False
			last = 0
			self.subwindows = []
			for step in border_arr + [self.width]:
				self.subwindows.append(Window(self.x+last, self.y, step-last, self.height))
				last = step

	def add_histogram(self, values=[], bins=10):
		if self.subwindows is not None:
			raise ValueError("Warning: You are adding content but already have subwindows!")
		self.content = Histogram(self.x, self.y, self.width, self.height, values, bins)

	def add_lineplot(self, xvals=[], yvals=[]):
		if self.subwindows is not None:
			raise ValueError("Warning: You are adding content but already have subwindows!")
		self.content = Lineplot(self.x, self.y, self.width, self.height, xvals, yvals)

	def draw(self):
		if self.content is None and self.subwindows is None:
			draw.rectangle((self.x,self.y,self.width,self.height), outline=0, fill=1)
		elif self.subwindows is not None:
			for subwin in self.subwindows:
				subwin.draw()
		else:
			self.content.draw()

class Lineplot:
	def __init__(self, x, y, width, height, xvals, yvals):
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.set_values(xvals, yvals)

	def set_values(self, xvals, yvals):
		if len(xvals) != len(yvals):
			raise ValueError("X and Y must be of equal length!")
		self.xvals = xvals
		self.yvals = yvals
		if len(xvals) > 0:
			self.xmin = min(xvals)
			self.ymin = min(yvals)
			self.xspan = float(max(xvals) - self.xmin)
			self.yspan = float(max(yvals) - self.ymin)

	def __get_px_coord(self, xval, yval):
		px_x = self.x + self.width * (xval - self.xmin) / self.xspan
		px_y = self.y + self.height * (1 - (yval - self.ymin) / self.yspan)
		return px_x, px_y

	def draw(self):
		draw.rectangle((self.x,self.y,self.x+self.width-1,self.y+self.height-1), outline=0, fill=0)
		if len(self.xvals) == 0:
			pass
		elif len(self.xvals) == 1:
			draw.line((self.x, self.y+self.height/2, self.x+self.width, self.y+self.height/2), fill=1)
		else:
			lastpair = None
			for pair in zip(self.xvals, self.yvals):
				if lastpair is None:
					lastpair = self.__get_px_coord(*pair)
				else:
					currentpair = self.__get_px_coord(*pair)
					draw.line(lastpair+currentpair, fill=1)
					lastpair = currentpair

class Histogram:
	def __init__(self, x, y, width, height, values, bins=10):
		if width < bins:
			raise ValueError("Reduce number of bins when creating a small histogram!")
		self.x = x
		self.y = y
		self.width = width
		self.height = height
		self.bins = bins
		self.bin_width = width / bins
		self.bin_shift = (width % bins) / 2
		self.set_values(values)

	def set_values(self, values):
		self.values = values
		if len(values) == 0:
			self.bin_heights = [0]*self.bins
		else:
			dmin, dmax = min(values), max(values)
			diff = dmax-dmin
			if diff == 0:
				self.bin_heights = [0]*self.bins
				self.bin_heights[self.bins/2] = self.height
			else:
				bin_data_width = diff / float(self.bins)
				bin_counts = [0]*self.bins
				for val in values:
					i = int((val - dmin) / bin_data_width)
					if i == self.bins:
						i -= 1
					bin_counts[i] += 1
				maxcount = float(max(bin_counts))
				px_per_count = (self.height-1) / maxcount
				self.bin_heights = [int(count * px_per_count) for count in bin_counts]

	def __draw_bar(self, bar_nr):
		x1 = self.x + self.bin_shift + self.bin_width*bar_nr
		y1 = self.y + self.height-1
		x2 = x1 + self.bin_width-1
		y2 = y1 - self.bin_heights[bar_nr]
		draw.rectangle((x1, y1, x2, y2), outline=1, fill=1)

	def draw(self):
		draw.rectangle((self.x,self.y,self.x+self.width-1,self.y+self.height-1), outline=0, fill=0)
		for i in range(self.bins):
			self.__draw_bar(i)

# Create root Window
rootwin = Window(0, 0, 128, 64)
rootwin.create_subwindows([32])
rootwin.subwindows[0].add_lineplot()
lower_win = rootwin.subwindows[1]
lower_win.create_subwindows([64], vertical=False)
lower_win.subwindows[0].add_histogram(bins=20)
lower_win.subwindows[1].add_histogram(bins=20)

print lower_win.x, lower_win.y, lower_win.width, lower_win.height

# Clear initially
rootwin.draw()
disp.image(image)
disp.display()

'''
CALLBACKS
'''

def show_message(msg):
	# Clear image buffer by drawing a white filled box.
	draw.rectangle((0,0,width,height), outline=0, fill=0)

	# Draw message
	for item in msg:
		draw.text(item[0], item[1], font=font, fill=1)

	# Draw the image buffer.
	disp.image(image)
	disp.display()


import json
datalog = []
def handle_data(data):
	print("Data:", data)
	data = json.loads(data)
	datalog.append(data)
	A = [d["a"] for d in datalog]
	T = [d["t"] for d in datalog]
	rootwin.subwindows[0].content.set_values(A, T)
	B = [d["b"] for d in datalog]
	lower_win.subwindows[0].content.set_values(A)
	lower_win.subwindows[1].content.set_values(B)
	rootwin.draw()
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
	client.subscribe("testing/oled/graphs")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	if msg.topic == "testing/oled/graphs":
		handle_data(msg.payload)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("broker.hivemq.com", 1883, 8000)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
