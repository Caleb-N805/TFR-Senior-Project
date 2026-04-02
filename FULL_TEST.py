#region --- Imports

import functions_test_alpha as f
import functions_analysis as g

from pathlib import Path
import sys
import time
import math

#endregion

#region --- Inputs

# Initialization Inputs

t_chuck = 20 # Chuck Temperature (°C)
i_initial = .5e-2 # Initial Current I1 (Amps)
f_current = 1.05 # Current Multiplier
film_thickness = 200 # Film thickness in nm
tcr_ref = .0061
i_limit = .1 # Amps
v_limit = 20 # Volts
initialization_time_delay = 2 # seconds
convergence_time_delay = 3 # seconds
mode = 2 # wire
#f.get_TCR(film_thickness) # TCR in K^-1

# Temperature Staircase Inputs
t_test = 140 # Test Temperature (°C)
f_power = 2 # Convergence factor
dt = 8 # Step Temperature (°C)
B_E = 3 # Temperature error band (°C)
F_corr = 1 # Correction factor
#endregion

'''Initialization'''

#region --- Setup and Configuration

# Initialize log file, which defines A_log_path, headers, start_func_time
prefix = "A"
A_log_path, headers, start_func_time = f.initialize_log_file(prefix)

resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR' # Fixed resource ID for Keithley 2450
smu, rm = f.initialize_smu(resource_id) # Initializes SMU

f.top_message(A_log_path, "A -- Initialization\n") # Header for .csv file

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
        r_chuck = f.measure_resistance_2wire(smu, 1e-3)
    else:
        r_chuck = f.measure_resistance_4wire(smu, 1e-3)

    print(f"R_chuck: {r_chuck:.4f} Ω")

    f.csvheader(A_log_path, headers) # Sets headers

    #endregion

    # Skip 6.1.2. as TCR(Tref) = TCR(Tchuck), Tchuck is ambient temperature
    # 6.1.3. is done in "Initialization Inputs" above.

    #region --- 6.1.4. Control loop to measure the initial thermal resistance

    # Initialization of loop
    n = 1
    i_n = i_initial

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
            r_n = f.measure_resistance_2wire(smu, i_n)
        else:
            r_n = f.measure_resistance_4wire(smu, i_n)
        
        # Calculate Power (P = I^2 * R)
        p_n = (i_n ** 2) * r_n
        
        # Calculate Temperature Ti
        # Ti = T_chuck + (delta_R / (R_chuck * TCR))
        t_n = max(t_chuck, t_chuck + ((r_n - r_chuck) / (r_chuck * tcr_ref)))

        print(f"[{n}] I: {i_n:.4f} A | R: {r_n:.4f} Ω | P: {p_n:.2f} W | ΔT: {t_n - t_chuck:.2f} °C")
        f.printcsv(A_log_path, start_func_time, n, i_n * 1000, r_n, p_n, t_n, t_n - t_chuck)

        # Save data point
        results.append({'n': n, 'I': i_n, 'R': r_n, 'P': p_n, 'T': t_n})

        # 6.1.6: Check for failure
        if r_n >= r_fail_init or i_n > i_limit:
            print("!! FAILURE DETECTED: Resistance limit exceeded. Exiting.")
            break

        # --- Exit Condition Logic ---
        # Flowchart requires: T_i >= (T_chuck + 50) AND i >= 5
        if t_n >= (t_chuck + 50) and n >= 5:
            print("\nTarget temperature (+50°C) and iteration count (>=5) met.")
            print(f"Initialization loop finished with {n} loops completed.")
            break

        # If no failure, set arbitrary delay before next loop
        time.sleep(initialization_time_delay)
        
        # Increment for next iteration
        i_n *= f_current
        n += 1

    #endregion

    # User confirmation of finished loop
    print(f"\nLoop Finished. Collected {len(results)} data points.")
    print("\nNumber of iterations was", n)

    #region --- 6.1.7: Proceed to Determination of Rth
    
    r_th, t_0_1, R_squared = g.analyze_power_vs_temp(A_log_path)
    print("\nR_th: ", r_th)
    print("\nT_0_1: ", t_0_1)
    print("\nR^2: ", R_squared)

    #endregion

finally:
    t_initialization = t_n # Define t_initialization as temperature at end of initialization
    print("Initialization phase complete.\n")





''' Temperature Staircase and Convergence '''





#region --- Setup and Configuration

# Initialize log file, which defines B_log_path, headers, start_func_time
prefix = "B"
B_log_path, headers, start_func_time = f.initialize_log_file(prefix)

f.top_message(B_log_path, "B -- Temperature Staircase\n") # Header for .csv file

#endregion

#region --- 6.2.1: Calculate temperature step and staircase temperature limit

t_stair = t_test - f_power * dt
print("Staircase temperature is", t_stair)

#endregion

#region --- 6.2.2: Instrument range and voltage compliance for staircase, convergence, stress phases

p_test = (t_test - t_0_1) / r_th # Estimated power at target stress temperature
#print("\nEstimated power at target stress temperature is", p_test)
r_test = r_chuck * (1 + tcr_ref * ((t_test / F_corr) - t_chuck)) # Estimated resistance at target stress temperature
#print("\nEstimated resistance at target stress temperature is", r_test)

c_limit = math.sqrt(p_test / r_test) # Amps
v_limit = math.sqrt(p_test * r_test) # Volts

#endregion

time.sleep(10)

''' TEST '''


try:
    f.csvheader(B_log_path, headers) # Print CSV header to log file
    
    #region --- 6.2.3: Set temperature ramp iteration
    
    n_stair = (t_stair - (t_initialization)) / dt

    #endregion

    # Initialization of loop
    n = 1
    # Data storage 
    results = []

    print("\nStarting Control Loop...")
    while True:

        if n == 1:
            t_n_1 = t_initialization

        if t_n_1 <= t_stair: 
            #region --- 6.2.3.1: Iterative power calculation (staircase)
            t_est = (t_n_1) + dt # Estimate temperature at next step
            #print("\nEstimated temperature for next step is ", t_est)

            p_est = (t_est - t_0_1) / r_th # Estimate electrical power necessary to reach t_i
            #print("\nEstimated power for next step is ", p_est)

            #endregion
        else:
            #region --- 6.2.3.1: Iterative power calculation (convergence)
            
            dP = ((t_test + (B_E / 2) - t_n_1)) / r_th
            print("\ndP is", dP)
            p_est = (dP/f_power) + p_n_1
            print("\np_est is", p_est)

            t_est = t_0_1 + (r_th * p_est)
            print("\nt_est is", t_est)
            
            #endregion

        #region --- 6.2.3.2: Iterative forcing current calculation
        
        # (c)
        r_est = r_chuck * (1 + tcr_ref * ((t_est / F_corr) - t_chuck)) # Estimated resistance at target stress temperature
        print("\nEstimated resistance is ", r_est)
        
        # (d)
        i_n = math.sqrt(p_est / r_est) # Calculate new forcing current to heat line to t_est

        # (e)
        # Apply forcing current and measure resistance
        if mode == 2:
            r_n = f.measure_resistance_2wire(smu, i_n)
        else:
            r_n = f.measure_resistance_4wire(smu, i_n)

        #endregion
        
        #region --- 6.2.3.3: Iterative thermal resistance calculation

        # (f) Calculate power dissipated and temperature
        p_n = (i_n ** 2) * r_n
        t_n = t_chuck + ((r_n - r_chuck)/(r_chuck * tcr_ref))
        
        # (g) Obtain new value for thermal resistance and intercept
        r_th, t_0_1, R_squared = g.B_analyze_power_vs_temp(t_n, A_log_path, B_log_path)
        print(f"\nR_th: {r_th:.4f}, t_0_1: {t_0_1:.4f}, R_squared: {R_squared:.4f}")
        

        print(f"[{n}] I: {i_n:.4f} A | R: {r_n:.4f} Ω | P: {p_n:.2f} W | ΔT: {t_n - t_chuck:.2f} °C | T: {t_n:.2f} C")
        f.printcsv(B_log_path, start_func_time, n, i_n * 1000, r_n, p_n, t_n, t_n - t_chuck)

        # Save data point
        results.append({'n': n, 'I': i_n, 'R': r_n, 'P': p_n, 'T': t_n})

        #endregion

        #region --- 6.2.4: Temporary failure criteria for staircase and convergence phases

        r_fail = r_est * (100 + 20)/100

        r_absfail = 100 * (abs(r_n - r_est) / min(r_n, r_est))
        if r_absfail >= 20:
            print("you done fucked up")
            break
        
        #endregion
        
        # --- Exit Condition Logic ---
        # Flowchart requires: T_n >= (T_test)
        if t_n >= t_test - B_E/2:
            print(f"\nTarget temperature {t_test} met.")
            print(f"Temperature Staircase loop finished with {n} loops completed.")
            break

        # Set arbitrary delay
        time.sleep(convergence_time_delay)

        # Increment for next iteration
        t_n_1 = t_n
        p_n_1 = p_n
        n += 1

    # Print number of iterations
    print("Number of iterations was", n)



finally:
    # Safety: Always turn off output and close connection
    smu.write("smu.source.output = smu.OFF")
    smu.close()
    rm.close()
    print("Instrument safely disconnected.")

#endregion
