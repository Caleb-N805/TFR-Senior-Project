import functions_test as f
import functions_analysis as g
import sys
import time
import json
import threading
from pathlib import Path
import csv

# Initialization Inputs
t_chuck = 20 # Chuck Temperature (°C)
i_initial = 10 / 1000 # Initial Current I1 (Amps)
f_current = 1.05 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_ref = .0003
c_limit = 1.05 # Amps
v_limit = 20 # Volts
#f.get_TCR(film_thickness) # TCR in K^-1

def last_25_average_dydx(x_values, y_values):

    dydx_values = []

    # Last 25 intervals use the last 26 points
    for i in range(len(x_values) - 25, len(x_values)):
        dx = x_values[i] - x_values[i - 1]
        dy = y_values[i] - y_values[i - 1]

        dydx_values.append(dy / dx)

    average_dydx = sum(dydx_values) / len(dydx_values)

    if average_dydx > 0:
        return "positive"
    else:
        return "negative"

# Create filename

filename = input("TFR Name: ")

# Threading
stop = False

def wait_for_enter():
    global stop
    input("Press Enter to stop...\n")
    stop = True

# Start the input listener in a separate thread
threading.Thread(target=wait_for_enter, daemon=True).start()

# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
f.config_4wire_resistance_mode(smu, v_limit) 

r_chuck = f.measure_resistance_4wire(smu, .05) 
print(f"R_chuck: {r_chuck:.4f} Ω")

time.sleep(5)

r_list = []
t_list = []
i_list = []

minimum = False
iterations = 0

start_time = time.time()

while not stop:
    elapsed = time.time() - start_time

    resistance = f.measure_resistance_4wire(smu, 1)

    r_list.append(resistance)
    t_list.append(elapsed)
    i_list.append(1)

    if iterations > 25:
        if last_25_average_dydx(t_list, r_list) == "positive" and minimum == False:
            print(f"Minimum hit at time {elapsed:.1f} s")
            minimum = True

    if resistance > 19.99:
        break

    iterations += 1

print(f"Time elapsed: {elapsed:.1f} s")

# Safety: Always turn off output and close connection
f.measure_resistance_4wire(smu, 0.001)
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")

with open(f'misctest{filename}.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    # Optional: Write a header
    writer.writerow(['time', 'resistance', 'current'])
    # Pair the lists and write them as rows

    writer.writerows(zip(t_list, r_list, i_list))

