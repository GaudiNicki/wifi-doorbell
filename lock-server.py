from flask import Flask
from flask import jsonify

from gpiozero import LED
from time import sleep

relay = LED(16)

app = Flask('lock-server')

@app.route('/unlock', methods=['GET'])
def unlockDoor():
	relay.on()
	sleep(20)
	relay.off()

	return jsonify(message='Door successfully unlocked')
app.run(host='0.0.0.0', port=80)
