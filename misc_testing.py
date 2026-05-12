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

c_test = .5 # Amps

# Function that returns average dr/dt of last 25 values
def last_25_average_drdt(t_values, r_values):

    drdt_values = []

    # Last 25 intervals use the last 26 points
    for i in range(len(t_values) - 25, len(t_values)):
        dt = t_values[i] - t_values[i - 1]
        dr = r_values[i] - r_values[i - 1]

        drdt_values.append(dr / dt)

    average_drdt = sum(drdt_values) / len(drdt_values)

    if average_drdt > 0:
        return "positive"
    else:
        return "negative"

# Function that returns average t and minimum r of last 25 values
def last_25_average_min_values(t_values, r_values):
    last_25_t = t_values[-25:]
    last_25_r = r_values[-25:]

    t_avg = sum(last_25_t) / len(last_25_t)
    r_min = min(last_25_r)

    return t_avg, r_min

#endregion


#region --- Log File Initialization

# Create log file for individual test (user input values)
wafer_number = input("Wafer: (ex. W4)")
die_number = input("Die: (ex. G3)")
resistor_number = input("Resistor: (ex. 0, 100, 500, SA, SB)")

# Define log file path for individual test
log_folder = Path("misc_testing_logs")
log_folder.mkdir(parents=True, exist_ok=True) # Check that log folder exists
log_path = log_folder / f"misctest-{wafer_number}-{die_number}-{resistor_number}.csv"

# Define main log file path for ALL tests and all results
main_log_folder = Path("misc_testing_logs")
main_log_folder.mkdir(parents=True, exist_ok=True) # Check that log folder exists
main_log_path = log_folder / f"misctest-MAIN.csv"

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

# Measure initial resistance
r_chuck = f.measure_resistance_4wire(smu, c_test) 
print(f"R_chuck: {r_chuck:.4f} Ω")

time.sleep(5)

# Initialize lists
r_list = []
t_list = []
i_list = []

# Setup for minimum function
minimum = False
iterations = 0

start_time = time.time() # Start test

while not stop:
    elapsed = time.time() - start_time # Time elapsed

    resistance = f.measure_resistance_4wire(smu, c_test)

    # Add values to lists
    r_list.append(resistance)
    t_list.append(elapsed)
    i_list.append(c_test)

    if iterations > 25: # Need to have at least 25 iterations to find minimum
        if last_25_average_drdt(t_list, r_list) == "positive" and minimum == False:
            t_min, r_min = last_25_average_min_values(t_list, r_list)
            print(f"t_min: {t_min:.1f} s")
            print(f"R_min: {r_min:.1f} ohms")
            minimum = True # Can't have minimum again

    if resistance > 19.99: # This only happens at failure, will automatically stop program
        print("TFR failed, voltage limit exceeded.")
        break

    iterations += 1

t_fail = elapsed # Time to failure
print(f"t_fail: {t_fail:.1f} s")

# Safety: Always turn off output and close connection
f.measure_resistance_4wire(smu, 0.001) # Set current to .001A so that when program runs again, it doesn't fry resistor
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")

#endregion


# Adjusted list for resistance tracking change in resistance compared to minimum
r_adjusted_list = [r - r_min for r in r_list]

# Device lifetime (only considering Joule heating)
t_device_lifetime = t_fail - t_min

#region --- Write log files

# Write log file
with open(log_path, 'w', newline='') as f:
    writer = csv.writer(f)
    # Optional: Write a header
    writer.writerow(['t', 'R - R_min', 'R', 'I'])
    # Pair the lists and write them as rows
    writer.writerows(zip(t_list, r_adjusted_list, r_list, i_list))

# Append main results
with open(main_log_path, 'a', newline='') as f:
    writer = csv.writer(f)
    # Pair the lists and write them as rows
    writer.writerow(wafer_number, die_number, resistor_number, t_device_lifetime, t_fail, t_min, r_chuck, r_min, c_test)

#endregion
