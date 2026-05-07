import functions_test as f
import functions_analysis as g
import sys
import time
import json
import threading
from pathlib import Path

# Initialization Inputs
t_chuck = 20 # Chuck Temperature (°C)
i_initial = 10 / 1000 # Initial Current I1 (Amps)
f_current = 1.05 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_ref = .0003
c_limit = 2 # Amps
v_limit = 10 # Volts
#f.get_TCR(film_thickness) # TCR in K^-1

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

r_chuck = f.measure_resistance_4wire(smu, .005) 
print(f"R_chuck: {r_chuck:.4f} Ω")

r_list = []
t_list = []

start_time = time.time()

while not stop:
    elapsed = time.time() - start_time

    r_list.append(f.measure_resistance_4wire(smu, 1))
    t_list.append(elapsed)

# Safety: Always turn off output and close connection
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")
