import functions_test_alpha as f
import functions_analysis as g
import sys
import time
import json
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

'''
log_folder = Path("logs")
log_path, headers, start_func_time = f.initialize_log_file("A")
print(log_path)

f.top_message(log_path, "Script A: Initialization\n")
f.csvheader(log_path, headers)
f.printcsv(log_path, start_func_time, 1, 2, 3, 4, 5, 6)

'''

csv_path = r"C:\Users\caleb\OneDrive\Desktop\Senior Project\TFR-Senior-Project\logs\log_2026.02.12_11.49.09.csv"
g.analyze_power_vs_temp(csv_path)

'''
# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)
f.tprint("Program Start")

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
f.config_2wire_resistance_mode(smu, v_limit) 

r_chuck = f.measure_resistance(smu, 1e-2) 
print(f"R_chuck: {r_chuck:.4f} Ω")

# Safety: Always turn off output and close connection
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")
'''