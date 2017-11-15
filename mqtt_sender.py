import math
import time

'''
MQTT STUFF
'''

import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	print "Connected: " + str(rc)

client = mqtt.Client()
client.on_connect = on_connect

import json
settings = json.load(open("settings.json"))

client.connect(settings["broker"], settings["port"])

import random
while True:
	vals = {"norm":random.normalvariate(0,1), "beta":random.betavariate(2,3), "time":time.time()}
	pl = json.dumps(vals)
	print "Publishing:", pl
	client.publish("testing/oled/graphs", payload=pl)
	time.sleep(1)
