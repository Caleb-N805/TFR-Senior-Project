#region --- Imports

import functions_test_alpha as f
import functions_analysis as g
import sys
import time

#endregion

#region --- Initialization Inputs

t_chuck = 20 # Chuck Temperature (°C)
i_initial = .5e-2 # Initial Current I1 (Amps)
f_current = 1.02 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_ref = .0061
c_limit = .1 # Amps
v_limit = 20 # Volts
time_delay = .5 # seconds
mode = 2 # wire
#f.get_TCR(film_thickness) # TCR in K^-1

#endregion

#region --- Setup and Configuration

# Initialize log file, which defines log_path, headers, start_func_time
prefix = "A"
log_path, headers, start_func_time = f.initialize_log_file(prefix)

resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR' # Fixed resource ID for Keithley 2450
smu, rm = f.initialize_smu(resource_id) # Initializes SMU

f.top_message(log_path, "A -- Initialization\n") # Header for .csv file

# Configure for Current Sourcing and 2-wire or 4-wire mode:
if mode == 2:
    f.config_2wire_resistance_mode(smu, v_limit) 
else:
    f.config_4wire_resistance_mode(smu, v_limit)

#endregion

''' TEST '''

try:

    #region --- 6.1.1. Measure the resistance at chuck temperature

    # Measure initial resistance (R_chuck) at a very low current
    # (e.g., 100uA) to prevent self-heating during the baseline
    
    print("\nMeasuring baseline R_chuck...")
    if mode == 2:
        r_chuck = f.measure_resistance_2wire(smu, 1e-2)
    else:
        r_chuck = f.measure_resistance_4wire(smu, 1e-2)

    print(f"R_chuck: {r_chuck:.4f} Ω")

    f.csvheader(log_path, headers) # Sets headers

    #endregion

    # Skip 6.1.2. as TCR(Tref) = TCR(Tchuck), Tchuck is ambient temperature
    # 6.1.3. is done in "Initialization Inputs" above.

    #region --- 6.1.4. Control loop to measure the initial thermal resistance

    # Initialization of loop
    i = 1
    current_i = i_initial

    # Data storage for 6.1.7 determination
    results = []

    # Calculate 6.1.6. failure resistance (r_fail_init)
    r_fail_init = 2 * r_chuck * (1 + (tcr_ref * 50))
    print("Resistance limit is ", r_fail_init)

    print("\nStarting Control Loop...")

    while True:
        # 6.1.5: Apply forcing current and measure resistance
        # Logic matches the gray box in your flowchart
        if mode == 2:
            r_i = f.measure_resistance_2wire(smu, current_i)
        else:
            r_i = f.measure_resistance_4wire(smu, current_i)
        
        # Calculate Power (P = I^2 * R)
        p_i = (current_i ** 2) * r_i
        
        # Calculate Temperature Ti
        # Ti = T_chuck + (delta_R / (R_chuck * TCR))
        t_i = max(t_chuck, t_chuck + ((r_i - r_chuck) / (r_chuck * tcr_ref)))

        print(f"[{i}] I: {current_i:.4f} A | R: {r_i:.4f} Ω | P: {p_i:.2f} W | ΔT: {t_i - t_chuck:.2f} °C")
        f.printcsv(log_path, start_func_time, i, current_i * 1000, r_i, p_i, t_i, t_i - t_chuck)

        # Save data point
        results.append({'i': i, 'I': current_i, 'R': r_i, 'P': p_i, 'T': t_i})

        # 6.1.6: Check for failure
        if r_i >= r_fail_init or current_i > c_limit:
            print("!! FAILURE DETECTED: Resistance limit exceeded. Exiting.")
            break

        # --- Exit Condition Logic ---
        # Flowchart requires: T_i >= (T_chuck + 50) AND i >= 5
        if t_i >= (t_chuck + 50) and i >= 5:
            print("\nTarget temperature (+50°C) and iteration count (>=5) met.")
            print(f"Initialization loop finished with {i} loops completed.")
            break

        # If no failure, set arbitrary delay before next loop
        time.sleep(time_delay)
        
        # Increment for next iteration
        current_i *= f_current
        i += 1

    #endregion

    # User confirmation of finished loop
    print(f"\nLoop Finished. Collected {len(results)} data points.")
    print("\nNumber of iterations was", i)

    #region --- 6.1.7: Proceed to Determination of Rth
    
    R_th, T_0_1, r_squared = g.analyze_power_vs_temp(log_path)
    print("\nR_th: ", R_th)
    print("\nT_0_1: ", T_0_1)
    print("\nR^2: ", r_squared)

    #endregion

finally:
    # Safety: Always turn off output and close connection
    smu.write("smu.source.output = smu.OFF")
    smu.close()
    rm.close()
    print("Instrument safely disconnected.")