import pyvisa
import time

rm = pyvisa.ResourceManager()
# Use your specific address here
smu = rm.open_resource('USB0::0x05E6::0x2450::04419551::INSTR')

try:
    # 1. Clear status and reset
    smu.write("reset()") 

    # 2. Set Sense Function to Voltage
    # Note: In TSP, we use dot notation, no colons!
    smu.write("smu.measure.func = smu.FUNC_DC_VOLTAGE")

    # 3. Enable 4-Wire (Remote Sense)
    smu.write("smu.measure.sense = smu.SENSE_4WIRE")

    # 4. Set Source Function and Level
    smu.write("smu.source.func = smu.FUNC_DC_VOLTAGE")
    smu.write("smu.source.level = 1.0")
    
    # 5. Set Current Limit (Compliance)
    smu.write("smu.source.ilimit.level = 0.1")

    print("4-Wire Sense (TSP) Enabled and Source Configured.")

    # 6. Turn on output and read
    smu.write("smu.source.output = smu.ON")
    time.sleep(0.5)
    
    # In TSP, we use smu.measure.read() to get data
    current_val = smu.query("print(smu.measure.read())")
    print(f"Measured Value: {current_val.strip()}")

    smu.write("smu.source.output = smu.OFF")

finally:
    smu.close()
    rm.close()