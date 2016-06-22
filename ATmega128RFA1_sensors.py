# Temperature from https://forums.synapse-wireless.com/showthread.php?t=1053
# Battery Voltage from https://forums.synapse-wireless.com/showthread.php?t=1775

""" ATMega 128 Temperature Sensor

   Notes:
    1. Each ATMega sensor varies by several degrees so it needs to be calibrated once for offset against
       the actual temperature and the offset stored in non-volatile memory. I recommend the Yocto sensor
       to calibrate against: http://www.yoctopuce.com/EN/products/usb-environmental-sensors/yocto-temperature
    2. Does not read and subtract voltage offset error of differential signal processor as suggested by datasheet
       because datasheet says it only makes 1 count difference, and above offset calculation will
       probably account for it.
    3. It also warms up several degrees if the SNAP is awake most of the time, so ambient measurements can
       only be made after a long sleep or low-duty-cycle wake time

"""


def atmega_temperature_read_raw():
    """ Read built-in temperature sensor """
    ADMUX = 0x7c
    ADCSRB = 0x7b
    ADCSRA = 0x7a
    ADCSRC = 0x77
    ADCL = 0x78
    ADCH = 0x79

    save_ADCSRA = peek(ADCSRA)
    save_ADCSRB = peek(ADCSRB)
    save_ADMUX = peek(ADMUX)
    save_ADCSRC = peek(ADCSRC)

    # Enable ADC
    # Clear ADATE, ADIE, and set prescaler to CPU Clk/32 = 500kHz
    my_ADCSRA = 0x95
    poke(ADCSRA, my_ADCSRA)     # enable ADC

    # Set channel and ref voltage
    poke(ADCSRB, 0x08)  # set MUX bit 5. Warning: have to set this before ADMUX or get bad result ... don't know why
    poke(ADMUX, 0xc9)   # Set 1.6 Vref and MUX bits 0-4. MUX = 101001 (binary)

    # Set Tracking time
    poke(ADCSRC, 0x02)  # >=20us start-up time and 0 hold time required for reading temperature

    # Wait for bit 7 (AVDDOK) and bit 5 (REFOK) to go high.
    while (peek(ADCSRB) & 0xa0) != 0xa0:
        pass

    # Begin conversion
    poke(ADCSRA, my_ADCSRA | 0x40)

    # Wait for conversion to complete
    while (peek(ADCSRA) & 0x10) != 0x10:
        pass

    # Read ADC (LSB first)
    Lbyte = peek(ADCL)
    Hbyte = peek(ADCH)
    val = Hbyte << 8 | Lbyte

    poke(ADCSRB, save_ADCSRB)
    poke(ADMUX, save_ADMUX)
    poke(ADCSRC, save_ADCSRC)
    poke(ADCSRA, save_ADCSRA)

    return val


def atmega_temperature_raw_to_dC(raw):
    """ Convert raw temperature value to deci-degreesC (tenths of a degree Celcius)
        Accuracy within 0.1 degC of ideal datasheet formula and works from -70 to +147 degC
        which is bigger than full operating range of ATMega: -40 to +85 degC
    """
    return (raw - 275) * 339 / 30 + 380


def atmega_ps_voltage():
    """ Return power supply voltage on ATMega128 platforms.
        Measures 1.7V to 3.675V
        Resolution is 75mV if V>=2.55V; and 50mV if V<=2.45V """

    mv = 3675
    i = 0x1f
    while True:
        poke(0x151, i)
        if peek(0x151) & 0x20:
            break
        if i == 0x10:
            mv = 2500
        if i > 0x10:
            mv -= 75
        else:
            mv -= 50
        i -= 1

    return mv
