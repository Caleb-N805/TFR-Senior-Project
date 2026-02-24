''' PRE TEST '''

#region --- Imports

import functions_test_alpha as f
import sys
import time
import math

#endregion

#region --- Temperature Staircase Inputs

# Temperature Staircase Inputs
t_chuck = 20 # Chuck Temperature (°C)
t_test = 200 # Test Temperature (°C)
f_power = 2 # Convergence factor
dt = 10 # Step Temperature (°C)
B_E = 1 # Temperature error band (°C)

# Slope and intercepts from line of best fit for P vs. T from Initialization
'''PLACEHOLDER VALUES'''
r_th = 116.99 # Thermal Resistance (°C/W)
T_0_1 = 16.02 # Temperature intercept (°C)
t_test = 1 # Temperature at start of test
r_chuck = 566 # Resistance at chuck temp
t_initialization = 71 # Temperature from end of initialization (°C)
F_corr = 1 # Correction factor

i_initial = .5e-2 # Initial Current I1 (Amps)
film_thickness = 200 # Film thickness in nm
tcr_chuck = .0061
time_delay = 0 # seconds

mode = 2 # wire
#f.get_TCR(film_thickness) # TCR in K^-1

#endregion

#region --- Setup and Configuration

# Initialize log file, which defines log_path, headers, start_func_time
prefix = "B"
log_path, headers, start_func_time = f.initialize_log_file(prefix)

resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR' # Fixed resource ID for Keithley 2450
smu, rm = f.initialize_smu(resource_id) # Initializes SMU

f.top_message(log_path, "A -- Initialization\n") # Header for .csv file

#endregion

#region --- 6.2.1: Calculate temperature step and staircase temperature limit

t_stair = t_test - f_power * dt
print("Staircase temperature is ", t_stair)

#endregion

#region --- 6.2.2: Instrument range and voltage compliance for staircase, convergence, stress phases

p_test = (t_test - T_0_1) / r_th # Estimated power at target stress temperature
r_test = r_chuck * (1 + tcr_chuck * ((t_test / F_corr) - t_chuck)) # Estimated resistance at target stress temperature

c_limit = math.sqrt(p_test / r_test) # Amps
v_limit = math.sqrt(p_test * r_test) # Volts

#endregion

# Configure for Current Sourcing and 2-wire or 4-wire mode:
if mode == 2:
    r_chuck = f.measure_resistance_2wire(smu, 1e-2) 
else:
    r_chuck = f.measure_resistance_4wire(smu, 1e-2)


''' TEST '''


try:
    f.csvheader() # Print CSV header to log file
    
    #region --- 6.2.3: Set temperature ramp iteration
    
    n_stair = (t_stair - (t_initialization)) / dt

    #endregion


    # Initialization of loop
    i = 1
    # Data storage 
    results = []

    print("\nStarting Control Loop...")
    while True:

        #region --- 6.2.3.1: Iterative power calculation (first iteration)

        if i == 1:
            t_i_1 = t_initialization

        t_est = (t_i_1) + dt # Estimate temperature at next step

        p_est = (t_est - T_0_1) / r_th # Estimate electrical power necessary to reach t_i

        #endregion
    
        #region --- 6.2.3.2: Iterative forcing current calculation
        
        r_est = r_chuck * (1 + tcr_chuck * ((t_est / F_corr) - t_chuck)) # Estimated resistance at target stress temperature
        
        current_i = math.sqrt(p_est / r_est) # Calculate new forcing current to heat line to t_est

        # Apply forcing current and measure resistance
        if mode == 2:
            r_i = f.measure_resistance_2wire(smu, current_i)
        else:
            r_i = f.measure_resistance_4wire(smu, current_i)


        #endregion
        
        # Calculate Power (P = I^2 * R)
        p_i = (current_i ** 2) * r_i
        
        # Calculate Temperature Ti
        # Ti = T_chuck + (delta_R / (R_chuck * TCR))
        t_i = t_chuck + ((r_i - r_chuck) / (r_chuck * tcr_chuck))

        
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


'''
# convergence 
    dP = ((t_test + B_E) / (2 - t_initialization)) / r_th

    p_i_con = (dP)/(f_power + )
'''