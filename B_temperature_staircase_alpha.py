''' PRE TEST '''


import functions_test_alpha as f
import sys
import time
import math

# Temperature Staircase Inputs
t_chuck = 20 # Chuck Temperature (°C)
t_test = 200 # Test Temperature (°C)
f_power = 2 # Convergence factor
dt = 10 # Step Temperature (°C)

# Slope and intercepts from line of best fit for P vs. T from Initialization
'''PLACEHOLDER'''
r_th = 116.99 # Thermal Resistance (°C/W)
t_0_1 = 16.02 # Temperature intercept (°C)
t_test = 1 # Temperature at start of test
r_chuck = 566 # Resistance at chuck temp
i_initial = .5e-2 # Initial Current I1 (Amps)
f_current = 1.05 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_chuck = .0061
time_delay = 0 # seconds
mode = 2 # wire
#f.get_TCR(film_thickness) # TCR in K^-1

# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)
f.tprint("Program Start")

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
if mode == 2:
    f.config_2wire_resistance_mode(smu, v_limit) 
else:
    f.config_4wire_resistance_mode(smu, v_limit)


''' TEST '''


try:

    # 6.2.1: Calculate temperature step and staircase temperature limit
    t_staircase = t_test - f_power * dt
    print("Staircase temperature is ", t_staircase)

    # 6.2.2: Instrument range and voltage compliance for staircase, convergence, stress phases
    if mode == 2:
        r_chuck = f.measure_resistance_2wire(smu, 1e-2) 
    else:
        r_chuck = f.measure_resistance_4wire(smu, 1e-2)

    p_test = (t_test - t_0_1) / r_th
    r_test = r_chuck * (1 + tcr_chuck * (t_test / (f_current * t_test) - t_chuck))

    c_limit = math.sqrt(p_test / r_test) # Amps
    v_limit = math.sqrt(p_test * r_test) # Volts

    f.csvheader()

    # --- 6.1.4: Initialization ---
    i = 1
    count = i
    current_i = i_initial
    r_fail_init = 2 * r_chuck * (1 + (tcr_ref * 50))
    print("Resistance limit is ", r_fail_init)
    
    # Data storage for 6.1.7 determination
    results = []

    print("\nStarting Control Loop...")
    while True:
        # 6.1.5: Apply forcing current and measure resistance
        # Logic matches the gray box in your flowchart
        r_i = f.measure_resistance(smu, current_i)
        
        # Calculate Power (P = I^2 * R)
        p_i = (current_i ** 2) * r_i
        
        # Calculate Temperature Ti
        # Ti = T_chuck + (delta_R / (R_chuck * TCR))
        t_i = max(t_chuck, t_chuck + ((r_i - r_chuck) / (r_chuck * tcr_ref)))
        
        print(f"[{i}] I: {current_i:.4f} A | R: {r_i:.4f} Ω | ΔT: {t_i - t_chuck:.2f} °C")
        f.printcsv(i, current_i * 1000, r_i, t_i - t_chuck)

        # 6.1.6: Check for failure
        if r_i >= r_fail_init or current_i > c_limit:
            print("!! FAILURE DETECTED: Resistance limit exceeded. Exiting.")
            break

        # Save data point
        results.append({'i': i, 'I': current_i, 'R': r_i, 'P': p_i, 'T': t_i})

        # Set arbitrary delay
        time.sleep(time_delay)

        # --- Exit Condition Logic ---
        # Flowchart requires: T_i >= (T_chuck + 50) AND i >= 5
        if t_i >= (t_chuck + 50) and i >= 5:
            print("\nTarget temperature (+50°C) and iteration count (>=5) met.")
            f.tprint(f"Initialization loop finished with {i} loops completed.")
            break
        
        # Increment for next iteration
        current_i *= f_current
        i += 1

    # 6.1.7: Proceed to Determination of Rth
    print(f"\nLoop Finished. Collected {len(results)} data points.")

    # Print number of iterations
    print("Number of iterations was", i)

finally:
    # Safety: Always turn off output and close connection
    smu.write("smu.source.output = smu.OFF")
    smu.close()
    rm.close()
    print("Instrument safely disconnected.")