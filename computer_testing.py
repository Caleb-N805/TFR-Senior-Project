#Sus
# Sigma
#banana
# Script purpose: connect to Keithley 2450 Power Supply
import pyvisa
rm = pyvisa.ResourceManager()
print(rm.list_resources())