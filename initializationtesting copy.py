import functionstesting as f
import sys
import time
import json

# Initilization Inputs
t_chuck = 20 # Chuck Temperature (°C)
i_initial = 10 / 1000 # Initial Current I1 (Amps)
f_current = 1.05 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_ref = .0003
c_limit = 2 # Amps
#f.get_TCR(film_thickness) # TCR in K^-1

# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)
f.tprint("Program Start")

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
f.config_2wire_resistance_mode(smu, vlimit=5) 

r_chuck = f.measure_resistance(smu, 1) 
print(f"R_chuck: {r_chuck:.4f} Ω")

# Safety: Always turn off output and close connection
smu.write("smu.source.output = smu.OFF")
smu.close()
rm.close()
print("Instrument safely disconnected.")