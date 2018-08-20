# Import package
import paho.mqtt.client as mqtt
import ssl, time, sys, json
import RPi.GPIO as GPIO
import csv
import os
import string
import threading

#Remote GPIO libraries
from gpiozero import LED
from gpiozero.pins.pigpio import PiGPIOFactory


# =======================================================
# Set Following Variables
# AWS IoT Endpoint
MQTT_HOST = "a3uegm2zc72ww9.iot.us-east-1.amazonaws.com" #Update to your Iot Endpoint
# CA Root Certificate File Path
CA_ROOT_CERT_FILE = "cert/VeriSign-Class 3-Public-Primary-Certification-Authority-G5 (1).pem"
# AWS IoT Thing Name
THING_NAME = "alexa123thing" #Change to your IOT Thing Name
# AWS IoT Thing Certificate File Path
THING_CERT_FILE = "cert/a5b8840f7f-certificate.pem.crt"
# AWS IoT Thing Private Key File Path
THING_PRIVATE_KEY_FILE = "cert/a5b8840f7f-private.pem.key"
# =======================================================


# =======================================================
# No need to change following variables
MQTT_PORT = 8883
MQTT_KEEPALIVE_INTERVAL = 45
SHADOW_UPDATE_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update"
SHADOW_UPDATE_ACCEPTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/accepted"
SHADOW_UPDATE_REJECTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/rejected"
SHADOW_UPDATE_DELTA_TOPIC = "$aws/things/" + THING_NAME + "/shadow/update/delta"
SHADOW_GET_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get"
SHADOW_GET_ACCEPTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get/accepted"
SHADOW_GET_REJECTED_TOPIC = "$aws/things/" + THING_NAME + "/shadow/get/rejected"
SHADOW_STATE_DOC_LED_ON = """{"state" : {"reported" : {"lights" : "on"}}}"""
SHADOW_STATE_DOC_LED_OFF = """{"state" : {"reported" : {"lights" : "off"}}}"""
# =======================================================



# Initiate MQTT Client
mqttc = mqtt.Client("client2")

#LED Control
def ledcontrol(bins):
    print('Turning on LED' + str(bins))
#!!!!!Change IP address to your PI Zero!!!!!!
    factory = PiGPIOFactory('192.168.1.100')#IP adress of Pi zero
    #led = LED(33, pin_factory=factory) # remote pin
    #led.off
    #led = LED(35, pin_factory=factory) # remote pin
    #led.off
    #led = LED(37, pin_factory=factory) # remote pin
    #led.off
    #led = LED(36, pin_factory=factory) # remote pin
    #led.off
    #led = LED(38, pin_factory=factory) # remote pin
    #led.off
    #led = LED(40, pin_factory=factory) # remote pin
    #led.off
    pin = 2
    if bins == 1:
        pin = 13
    if bins == 2:
        pin = 19
    if bins == 3:
        pin = 26
    if bins == 4:
        pin = 16
    if bins == 5:
        pin = 20
    if bins == 6:
        pin = 21
    led = LED(pin, pin_factory=factory) # remote pin
    led.on()
    time.sleep(30)
    led.off()
    
#CSV Function
def text2int(textnum, numwords={}):
	if not numwords:
		units = [
	        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
	        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
	        "sixteen", "seventeen", "eighteen", "nineteen",]

		tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

		scales = ["hundred", "thousand", "million", "billion", "trillion"]

		numwords["and"] = (1, 0)
		for idx, word in enumerate(units):    numwords[word] = (1, idx)
		for idx, word in enumerate(tens):     numwords[word] = (1, idx * 10)
		for idx, word in enumerate(scales):   numwords[word] = (10 ** (idx * 3 or 2), 0)

	current = result = 0
	for word in textnum.split():
		if word not in numwords:
			return True
			#raise Exception("Illegal word: " + word)

	scale, increment = numwords[word]
	current = current * scale + increment
	if scale > 100:
		result += current
		current = 0

	return result + current
	
def nextword(target, source):
	for i, w in enumerate(source):
		if w == target:
			return source[i+1]	

def updatecsv(myQuestion):
	#Declare 9 bin list matrix	
	bins= [[],[],[],[],[],[],[],[],[]]
	
	#Open CSV file and create a temp file for editing		
	csv_file = 'storageroom.csv'  # file to be updated
	tempfilename = os.path.splitext(csv_file)[0] + '.bak'
	try:
	    os.remove(tempfilename)  # delete any existing temp file
	except OSError:
	    pass
	os.rename(csv_file, tempfilename)

	# create a temporary list from the input file
	with open(tempfilename, mode='r') as infile:
	    reader = csv.reader(infile)
	    temp_list = list(reader)

	bins = temp_list
	result_list = []

	
	#Query variables to parse through
	whereis = ['where is my', 'find my','look for','where is']
	placein = ['place in container', 'put in container']
	removefrom = ['remove from container']
	binlocations = ''
	responsemsg = 'sorry I do not understand'

	for query in whereis:
		if query in myQuestion:
			querypos = myQuestion.rfind(query)
			findthis= myQuestion[querypos+len(query)+1:] 
			print(findthis)
			threads = [ ]
			for row in range(9):#Range 9 is total number of bins
				ledbin = row+1
				t1 = threading.Thread(target=ledcontrol, args=(ledbin,))
				if findthis in bins[row]:
					print(row-1)
					result_list.append(row)
					binlocations += str(row+1) + " , "
					threads.append(t1)
					t1.start()
					print('Start new thread')
			if len(result_list) == 0:
				print('No results')
				responsemsg = 'sorry there were no matches'

			if len(result_list) > 0:
				print('Match found')
				print(result_list)
				
				responsemsg = 'I found matches for ' + findthis + ' in bin ' + binlocations


	for query in placein:		
		if query in myQuestion:
			splitquestion = myQuestion.split()
			binnumber = nextword("container", splitquestion)

			print(binnumber)
			#need to update query to match one in whereis
			querypos = myQuestion.rfind(query + ' ' + binnumber) + len(query) + 1 + len(binnumber) + 1
			addthis= myQuestion[querypos:]
			print(addthis)
			if text2int(binnumber):
				bins[int(binnumber)-1].append(addthis)
			else:
				bins[text2int(binnumber)-1].append(addthis)
			responsemsg = 'ok ' + addthis + ' has been added to container ' + binnumber
			print(responsemsg)
			

	for query in removefrom:
		if query in myQuestion:
			splitquestion = myQuestion.split()
			binnumber = nextword("container", splitquestion)
			print(binnumber)

			querypos = myQuestion.rfind(query + ' ' + binnumber) + len(query) + 1 + len(binnumber) + 1
			removethis= myQuestion[querypos:]
			try:
				if text2int(binnumber):
					bins[int(binnumber)-1].remove(removethis)
				else:
					bins[text2int(binnumber)-1].remove(removethis)
				responsemsg = 'ok ' + removethis + ' has been removed from container ' + binnumber
				print(responsemsg)
				
			except:
				print('item not found')
				with open(csv_file, mode='wb', ) as outfile:
					writer = csv.writer(outfile)
					writer.writerows(bins)

				os.remove(tempfilename)  # delete backed-up original	
				responsemsg = 'sorry I did not find the ' + removethis + ' in bin ' + binnumber + ' to remove'
				return(responsemsg)
	
	#Create new CSV file in with newline='' to prevent extra lines
	#python 3 version = with open(csv_file, mode='w', newline='') as outfile:
	with open(csv_file, mode='wb', ) as outfile:
		writer = csv.writer(outfile)
		writer.writerows(bins)

	os.remove(tempfilename)  # delete backed-up original	
	return(responsemsg)

# Master LED Control Function
def LED_Status_Change(Shadow_State_Doc, Type):
	# Parse LED Status from Shadow
	DESIRED_LED_STATUS = ""
	print( "\nParsing Shadow Json..." + Shadow_State_Doc)
	SHADOW_State_Doc = json.loads(Shadow_State_Doc)
	if Type == "DELTA":
		if 'lights' in SHADOW_State_Doc['state']:
			DESIRED_LED_STATUS = SHADOW_State_Doc['state']['lights']
			responsemsg = '{"state" : {"reported" : {"lights" : "' + DESIRED_LED_STATUS + '"}}}'
			mqttc.publish(SHADOW_UPDATE_TOPIC,responsemsg,qos=1)
			responsemsg = '{"state" : {"desired" : {"response" : "' + updatecsv(DESIRED_LED_STATUS.lower()) + '"}}}'
			mqttc.publish(SHADOW_UPDATE_TOPIC,responsemsg,qos=1)
			
	elif Type == "GET_REQ":
		DESIRED_LED_STATUS = SHADOW_State_Doc['state']['desired']['lights']
	print( "Desired LED Status: " + DESIRED_LED_STATUS)





# Define on connect event function
# We shall subscribe to Shadow Accepted and Rejected Topics in this function
def on_connect(mosq, obj, rc, last):
	print( "Connected to AWS IoT...")
	print(last)
	# Subscribe to Delta Topic
	mqttc.subscribe(SHADOW_UPDATE_DELTA_TOPIC, 1)
	# Subscribe to Update Topic
	#mqttc.subscribe(SHADOW_UPDATE_TOPIC, 1)
	# Subscribe to Update Accepted and Rejected Topics
	mqttc.subscribe(SHADOW_UPDATE_ACCEPTED_TOPIC, 1)
	mqttc.subscribe(SHADOW_UPDATE_REJECTED_TOPIC, 1)	
	# Subscribe to Get Accepted and Rejected Topics
	mqttc.subscribe(SHADOW_GET_ACCEPTED_TOPIC, 1)
	mqttc.subscribe(SHADOW_GET_REJECTED_TOPIC, 1)


# Define on_message event function. 
# This function will be invoked every time,
# a new message arrives for the subscribed topic 
def on_message(mosq, obj, msg):
	if str(msg.topic) == SHADOW_UPDATE_DELTA_TOPIC:
		print( "\nNew Delta Message Received...")
		SHADOW_STATE_DELTA = str(msg.payload)
		print(SHADOW_STATE_DELTA)
		LED_Status_Change(SHADOW_STATE_DELTA, "DELTA")
	elif str(msg.topic) == SHADOW_GET_ACCEPTED_TOPIC:
		print( "\nReceived State Doc with Get Request...")
		SHADOW_STATE_DOC = str(msg.payload)
		print(SHADOW_STATE_DOC)
		LED_Status_Change(SHADOW_STATE_DOC, "GET_REQ")
	elif str(msg.topic) == SHADOW_GET_REJECTED_TOPIC:
		SHADOW_GET_ERROR = str(msg.payload)
		print("\n---ERROR--- Unable to fetch Shadow Doc...\nError Response: " + SHADOW_GET_ERROR)
	elif str(msg.topic) == SHADOW_UPDATE_ACCEPTED_TOPIC:
		print("\nLED Status Change Updated SUCCESSFULLY in Shadow...")
		print("Response JSON: " + str(msg.payload))
	elif str(msg.topic) == SHADOW_UPDATE_REJECTED_TOPIC:
		SHADOW_UPDATE_ERROR = str(msg.payload)
		print("\n---ERROR--- Failed to Update the Shadow...\nError Response: " + SHADOW_UPDATE_ERROR)
	else:
		print("AWS Response Topic: " + str(msg.topic))
		print("QoS: " + str(msg.qos))
		print("Payload: " + str(msg.payload))


def on_subscribe(mosq, obj, mid, granted_qos):
	#As we are subscribing to 3 Topics, wait till all 3 topics get subscribed
	#for each subscription mid will get incremented by 1 (starting with 1)
	if mid == 3:
		# Fetch current Shadow status. Useful for reconnection scenario. 
		mqttc.publish(SHADOW_GET_TOPIC,"",qos=1)

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Diconnected from AWS IoT. Trying to auto-reconnect...")



# Register callback functions
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect

# Configure TLS Set
mqttc.tls_set(CA_ROOT_CERT_FILE, certfile=THING_CERT_FILE, keyfile=THING_PRIVATE_KEY_FILE, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)

# Connect with MQTT Broker
mqttc.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)		

# Continue monitoring the incoming messages for subscribed topic
mqttc.loop_forever()


