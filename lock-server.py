from flask import Flask
from flask import jsonify

from gpiozero import LED
from time import sleep

##############################
#   Configure these params   #
##############################

# Relay pin
RELAY_PIN = 16

# port, on which your app runs
APP_PORT = 80

##############
#  Program   #
##############

relay = LED(RELAY_PIN)
app = Flask('lock-server')


@app.route('/unlock', methods=['GET'])
def unlock_door():
	relay.on()
	sleep(20)
	relay.off()

	return jsonify(message='Door successfully unlocked')


app.run(host='0.0.0.0', port=APP_PORT)
