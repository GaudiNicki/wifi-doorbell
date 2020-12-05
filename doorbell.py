############################
#  Configure this params!  #
############################

# Doorbell pin
DOORBELL_PIN = 19

# Your raspberry pi's ip address
RASPBERRYPI_LOCAL_IP = ''

# Number of seconds to keep the meeting active
MEETING_ACTIVE_S = 180

# ID of the JITSI meeting room
# if None then a random UUID is used as meeting id
JITSI_ID = None

# Path to the sound file, which is player after the doorbell is pushed
SOUNDFILE_PATH = '/home/pi/wifi-doorbell/doorbell.wav'

# Enables email notifications
ENABLE_EMAIL = True

# Enables ringing sound on doorbell press
ENABLE_RING = True

# Email address you want to send the notification from (only works with gmail)
FROM_EMAIL = ''

# You can generate an app password here to avoid storing your password in plain text
# this should also come from an environment variable
# https://support.google.com/accounts/answer/185833?hl=en
FROM_EMAIL_PASSWORD = ''

# Email you want to send the update to
TO_EMAIL = ''

#############
#  Program  #
#############

import time
import os
import signal
import subprocess
import smtplib
import uuid

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO. This is probably because you need superuser. Try running again with 'sudo'.")


def show_screen():
    os.system("vcgencmd display_power 1")


def hide_screen():
    os.system("vcgencmd display_power 0")


def send_email_notification(meeting_url):
    if ENABLE_EMAIL:
        unlock_url = 'http://%s/unlock' % RASPBERRYPI_LOCAL_IP

        sender = EmailSender(FROM_EMAIL, FROM_EMAIL_PASSWORD)
        email = Email(
            sender,
            'Wifi Doorbell',
            'Someone rang at your door!',
            'A visitor is waiting outside your door. If you want to talk to him click here: %s\n\n'
            'If you want to open the door for him, click here: %s'
            % (meeting_url, unlock_url)
        )
        email.send(TO_EMAIL)


def ring_doorbell(pin):
    # plays ring sound
    ring_sound = Sound(SOUNDFILE_PATH)
    ring_sound.play()

    # create and start Jitsi meeting
    meeting_id = JITSI_ID if JITSI_ID else str(uuid.uuid4())
    meeting = JitsiMeeting(meeting_id)
    meeting.start()

    # send email notification
    send_email_notification(meeting.get_meeting_url())

    # show jitsi meeting for DOORBELL_SCREEN_ACTIVE_S seconds and end meeting
    show_screen()
    time.sleep(MEETING_ACTIVE_S)
    meeting.end()
    hide_screen()


class Sound:
    def __init__(self, sound_path):
        self.sound_path = sound_path

    def play(self):
        if ENABLE_RING:
            subprocess.Popen(["omxplayer", "-o", "local", self.sound_path])


class JitsiMeeting:
    def __init__(self, meeting_id):
        self.meeting_id = meeting_id
        self._process = None

    def get_meeting_url(self):
        return "http://meet.jit.si/%s" % self.meeting_id

    def start(self):
        if not self._process and self.meeting_id:
            self._process = subprocess.Popen(["chromium-browser", "-kiosk", self.get_meeting_url()])
        else:
            print("Can't start jitsi meeting -- already started or missing meeting id")

    def end(self):
        if self._process:
            os.kill(self._process.pid, signal.SIGTERM)


class EmailSender:
    def __init__(self, email, password):
        self.email = email
        self.password = password


class Email:
    def __init__(self, sender, subject, preamble, body):
        self.sender = sender
        self.subject = subject
        self.preamble = preamble
        self.body = body

    def send(self, to_email):
        msgRoot = MIMEMultipart('related')
        msgRoot['Subject'] = self.subject
        msgRoot['From'] = self.sender.email
        msgRoot['To'] = to_email
        msgRoot.preamble = self.preamble

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)
        msgText = MIMEText(self.body)
        msgAlternative.attach(msgText)

        smtp = smtplib.SMTP('smtp.gmail.com', 587)
        smtp.starttls()
        smtp.login(self.sender.email, self.sender.password)
        smtp.sendmail(self.sender.email, to_email, msgRoot.as_string())
        smtp.quit()


class Doorbell:
    def __init__(self, doorbell_button_pin):
        self._doorbell_button_pin = doorbell_button_pin

    def run(self):
        try:
            print("Starting Doorbell...")
            hide_screen()
            self.setup_gpio()
            print("Waiting for doorbell rings...")
            self.wait_forever()

        except KeyboardInterrupt:
            print("Safely shutting down...")

        finally:
            self.cleanup()

    def wait_forever(self):
        while True:
            time.sleep(0.1)

    def setup_gpio(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._doorbell_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self._doorbell_button_pin, GPIO.RISING, callback=ring_doorbell, bouncetime=10000)

    def cleanup(self):
        GPIO.cleanup(self._doorbell_button_pin)
        show_screen()


if __name__ == "__main__":
    doorbell = Doorbell(DOORBELL_PIN)
    doorbell.run()