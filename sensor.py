# Copyright (C) 2016 Synapse Wireless, Inc.
# Subject to your agreement of the disclaimer set forth below, permission is given by Synapse Wireless, Inc. ("Synapse")
# to you to freely modify, redistribute or include this SNAPpy code in any program. The purpose of this code is to help
# you understand and learn about SNAPpy by code examples.
# BY USING ALL OR ANY PORTION OF THIS SNAPPY CODE, YOU ACCEPT AND AGREE TO THE BELOW DISCLAIMER. If you do not accept or
# agree to the below disclaimer, then you may not use, modify, or distribute this SNAPpy code.
# THE CODE IS PROVIDED UNDER THIS LICENSE ON AN "AS IS" BASIS, WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
# IMPLIED, INCLUDING, WITHOUT LIMITATION, WARRANTIES THAT THE COVERED CODE IS FREE OF DEFECTS, MERCHANTABLE, FIT FOR A
# PARTICULAR PURPOSE OR NON-INFRINGING. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE COVERED CODE IS WITH
# YOU. SHOULD ANY COVERED CODE PROVE DEFECTIVE IN ANY RESPECT, YOU (NOT THE INITIAL DEVELOPER OR ANY OTHER CONTRIBUTOR)
# ASSUME THE COST OF ANY NECESSARY SERVICING, REPAIR OR CORRECTION. UNDER NO CIRCUMSTANCES WILL SYNAPSE BE LIABLE TO
# YOU, OR ANY OTHER PERSON OR ENTITY, FOR ANY LOSS OF USE, REVENUE OR PROFIT, LOST OR DAMAGED DATA, OR OTHER COMMERCIAL
# OR ECONOMIC LOSS OR FOR ANY DAMAGES WHATSOEVER RELATED TO YOUR USE OR RELIANCE UPON THE SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGES OR IF SUCH DAMAGES ARE FORESEEABLE. THIS DISCLAIMER OF WARRANTY AND LIABILITY
# CONSTITUTES AN ESSENTIAL PART OF THIS LICENSE. NO USE OF ANY COVERED CODE IS AUTHORIZED HEREUNDER EXCEPT UNDER THIS
# DISCLAIMER.

"""
Example SNAPpy script for Data Collector sensors.

Returns:
  * Number of polls received since last restart
  * ATmega128RFA1 internal temperature in deci-degrees Celsius (dC)
  * ATmega128RFA1 power supply voltage in milliVolts (mV)
  * ADC Reading from external thermistor.
  * 0-99 reading for light level from photocell.

Also blinks an led each time it is polled.
"""

from snappyatmega.sensors import *
from snappyatmega.utils import adcRefSelect

GPIO_12 = 25
GPIO_18_ADC = 7
GPIO_11_ADC = 0

# Setting this to none will disable the blink
# LED_PIN = None

# 6 is GPIO_1 for SN-171 protoboards and SN-132 paddleboards,
# and the green led on SS200 / SN220 SNAPsticks.
LED_PIN = 6

NUM_POLLS = 0

thermisterAdcChannel = GPIO_18_ADC

photoCellPin = GPIO_12
photoCellAdcChannel = GPIO_11_ADC
requiredRange = 100
photoMax = 0x0000
photoMin = 0x03FF


def data():
    """Return the formatted data string"""
    # First, blink the LED
    pulsePin(LED_PIN, 1000, True)

    # Get the individual values
    num_polls = _get_poll_counter()

    raw_temp = atmega_temperature_read_raw()
    temp_dC = atmega_temperature_raw_to_dC(raw_temp)

    ps_mV = atmega_ps_voltage()

    ext_temp = readAdc(thermisterAdcChannel)

    photo_val = _read_photo()

    # Return as a CSV-formatted string
    return str(num_polls) + "," + str(temp_dC) + "," + str(ps_mV) + ',' + str(ext_temp) + ',' + str(photo_val)


@setHook(HOOK_STARTUP)
def _on_startup():
    # Initialize the LED
    setPinDir(LED_PIN, True)
    writePin(LED_PIN, False)

    _reset_poll_counter()
    _init_ext_sensors()


def _reset_poll_counter():
    """Reset the poll counter"""
    global NUM_POLLS
    NUM_POLLS = 0


def _init_ext_sensors():
    # Set up thermistor
    readAdc(thermisterAdcChannel)
    adcRefSelect(18)  # Force 1.8v ADC REF (default is 1.6v)

    # Set up photocell
    setPinDir(photoCellPin,True)
    writePin(photoCellPin, True) # Set the pin high to power the device
    _read_photo()  # take an initial reading to get things started


@setHook(HOOK_1S)
def _read_photo():
    """Get darkness value from photo cell reading, scaled 0-99"""
    global photoMax, photoMin

    # Sample the photocell
    curReading = readAdc(photoCellAdcChannel)

    # Auto-Calibrate min/max photocell readings
    if photoMax < curReading:
        photoMax = curReading
    if photoMin > curReading:
        photoMin = curReading

    if photoMax <= photoMin:
        return 0

    photoRange = photoMax - photoMin
    if photoRange < requiredRange:  # if not yet calibrated
        return 0

    # Remove zero-offset to get value in range 0-1024 (10-bit ADC)
    curReading -= photoMin

    # Scale 0-100, careful not to exceed 16-bit integer positive range (32768)
    curReading = (curReading * 10) / (photoRange / 10)

    # Return value scaled 0-99
    return (curReading * 99) / 100


def _get_poll_counter():
    """Increment and return the poll counter"""
    global NUM_POLLS
    NUM_POLLS += 1

    return NUM_POLLS
