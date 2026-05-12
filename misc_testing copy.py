# region --- Imports and Definitions

import functions_test as f
import functions_analysis as g
import sys
import time
import json
import threading
from pathlib import Path
import csv

c_limit = 1.05 # Amps
v_limit = 20 # Volts


#region --- Log File Initialization

# Create log file for individual test (user input values)
wafer_number = input("Wafer: (ex. W4)")
die_number = input("Die: (ex. G3)")
resistor_number = input("Resistor: (ex. 0, 100, 500, SA, SB)")

# Define log file path for individual test
log_folder = Path("misc_testing_logs")
log_folder.mkdir(parents=True, exist_ok=True) # Check that log folder exists
log_path = log_folder / f"misctest-{wafer_number}-{die_number}-{resistor_number}.csv"

#endregion


#region --- Threading (press Enter at any time to stop program)

# Threading
stop = False

def wait_for_enter():
    global stop
    input("Press Enter to stop...\n")
    stop = True

# Start the input listener in a separate thread
threading.Thread(target=wait_for_enter, daemon=True).start()

#endregion


#region --- Testing

# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
f.config_4wire_resistance_mode(smu, v_limit) 

# Initialize lists
r_list = []
i_list = []

import numpy as np

values = np.logspace(np.log10(0.000001), np.log10(1.05), 50)

for x in values:
    r_chuck = f.measure_resistance_4wire(smu, x) 
    print(f"R_chuck: {r_chuck:.4f} Ω")

    r_list.append(r_chuck)
    i_list.append(x)
    time.sleep(1)


# Safety: Always turn off output and close connection
f.measure_resistance_4wire(smu, 0.001) # Set current to .001A so that when program runs again, it doesn't fry resistor
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")

#endregion


#region --- Write log files

# Write log file
with open(log_path, 'w', newline='') as f:
    writer = csv.writer(f)
    # Optional: Write a header
    writer.writerow(['R', 'I'])
    # Pair the lists and write them as rows
    writer.writerows(zip(r_list, i_list))

