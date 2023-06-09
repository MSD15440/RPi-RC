# interface DYNM3876 ESC with Raspberry Pi
# credit to https://elinux.org/RPi_GPIO_Interface_Circuits for help
#
# ESC power button was removed and is now controlled by GPIO 23:
# the ESC power button is has 4 wires in this order:
# A red - carries 12v when the ESC has power
# B red - if the ESC has power, no voltage until button pressed
# C white - unimportant rn
# D black  - unimportant atm
# Connecting wires A and B turns on the ESC
#
# because the wires run at 12v, a relay is used to control them with the Pi:
# at present, the relay is a JS1E-6V, (janky current setup with parts I have)
# wire A is connected to pin 3 of the relay, which is Normally Open
# wire B is connected to pin 1 of the relay, aka COM
# pin 5 of the relay, one side of the coil, is connected to 5v supply
# the other side of the coil is pin 2, and is connected to the collector of a transistor

# pins 2 and 5 are connected with a diode to theoretically isolate the pi from 
# the inductive load of the relay the cathode of the diode is connected to 
# the positive supply rail
# this diode is currently Zener diode N5817 but I would use 1N4001 if i had it
#
# the transistor is an NPN 2N3904
# its base is connected to GPIO 23 of the pi through a 1k resistor
# its collector is connectd to pin 2 of the relay
# its emitter is connected to the ground of the 5v supply

from gpiozero import AngularServo
from time import sleep

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

from gpiozero.pins.pigpio import PiGPIOFactory
factory=PiGPIOFactory()

# set RPi 4b pins to be plugged in
ESC_POWER_PIN = 23
ESC_PWM_PIN = 13

# define throttle parameters
FULL_REV_THROTTLE = -90
NEUTRAL_THROTTLE = 0
FULL_FWD_THROTTLE = 90

# bare minumum throttles that will move the motor when 90 max -90 min
MIN_FWD_THROTTLE = 10.1
MIN_REV_THROTTLE = -8.1


# control the ESC through PWM by treating it as a servo
ESC = AngularServo(ESC_PWM_PIN, min_angle= FULL_REV_THROTTLE, max_angle=FULL_FWD_THROTTLE, min_pulse_width=1/1000, max_pulse_width=2/1000, pin_factory=factory)

# initialize the GPIO pin to switch on/off the ESC
GPIO.setup(ESC_POWER_PIN, GPIO.OUT)
GPIO.output(ESC_POWER_PIN, 0) # start with the pin off


# turn on the ESC
def pwrOn():
	print("powering on ESC")
	GPIO.output(ESC_POWER_PIN, 1) # turn on the ESC
	print("ESC on")


# just turn off the ESC 
def pwrOff():
	print("powering off ESC")
	GPIO.output(ESC_POWER_PIN, 0) # turn off the ESC
	print("ESC off")


# initialize the ESC by running the calibration routine:
def calibrate():
	print("calibrating:")
	print("setting max throttle")
	setThrottle(FULL_FWD_THROTTLE) # start at full throttle
	pwrOn()
	sleep(2) # hold full throttle for two seconds 
	print("should hear two beeps")
	sleep(1) # wait a second
	print("setting neutral throttle ")
	setThrottle(NEUTRAL_THROTTLE) 
	print("should hear long beep")
	sleep(2) # hold neutral throttle for two seconds
	print("ESC should be calibrated")
	print("normal startup noises:")
	print("first beeps: 3 for 3 cell battery, 4 for 4 cell")
	sleep(1)
	print("second beeps: 1 for brake on, 2 for brake off")
	sleep(1)
	print("ESC startup done")


def start():
	print("ESC starting up")
	setThrottle(NEUTRAL_THROTTLE)
	pwrOn()
	print("listen to the ESC beeps now")
	sleep(2)
	print("first beeps: 3 for 3 cell battery, 4 for 4 cell")
	sleep(2)
	print("second beeps: 1 for brake on, 2 for brake off")
	sleep(2)
	print("ESC startup done")
	

def fixThrottle(throttle):
	# handle forward throttle
	if throttle > NEUTRAL_THROTTLE:	
		# account for deadzone
		throttle += MIN_FWD_THROTTLE - 1
		
	# handle reverse throttle
	elif throttle < NEUTRAL_THROTTLE:
		throttle += MIN_REV_THROTTLE + 1 

	# cap throttle
	if throttle > FULL_FWD_THROTTLE:
		throttle = FULL_FWD_THROTTLE
	elif throttle < FULL_REV_THROTTLE:
		throttle = FULL_REV_THROTTLE
		
	return throttle


def setThrottle(throttle):
	adjustThrottle = fixThrottle(throttle)
	ESC.angle = adjustThrottle
	print("Throttle:", adjustThrottle, "/",u"\u00B1", FULL_FWD_THROTTLE)


def setThrottleRaw(throttle):
	ESC.angle = throttle
	print("Throttle:", throttle, "/",u"\u00B1", FULL_FWD_THROTTLE)


# if this isn't being called from another program do a little test routine
if __name__ == '__main__':
	try:
		calibrate()
		testvector = [1, 2, 3, 0, -1, -2, -3, 0]
		for i in testvector:
			setThrottle(i)
			sleep(2)
		pwrOff()


	except KeyboardInterrupt: # If CTRL+C is pressed, exit cleanly:
		print("Keyboard interrupt")

# except:
#    print("some error")  # commented out so that I find runtime python errors

	finally:
		print("clean up") 
		setThrottle(0)
		pwrOff()
		GPIO.cleanup() # cleanup all GPIO 
