# Script purpose: connect to Keithley 2450 Power Supply

import pyvisa

# 1. Initialize the Resource Manager
rm = pyvisa.ResourceManager()

# 2. List all available resources (USB, GPIB, LAN, etc.)
# Run this once to find your instrument's specific address
print("Available Resources:", rm.list_resources())

# 3. Connect to the instrument
# Replace this string with your actual device address from the list above
# Example USB: 'USB0::0x05E6::0x2450::04425317::INSTR'
# Example LAN: 'TCPIP0::192.168.1.50::inst0::INSTR'
resource_name = 'USB0::0x05E6::0x2450::04425317::INSTR' 

try:
    smu = rm.open_resource(resource_name)
    smu.timeout = 5000  # Set timeout to 5 seconds
    
    # 4. Identify the instrument
    idn = smu.query("*IDN?")
    print(f"Successfully connected to: {idn}")

    # Reset to default settings
    smu.write("*RST")

finally:
    # Always close the connection when finished
    smu.close()
    rm.close()