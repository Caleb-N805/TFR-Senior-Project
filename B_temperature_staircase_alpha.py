''' PRE TEST '''

#region --- Imports

import functions_test_alpha as f
import functions_analysis as g

from pathlib import Path
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
F_corr = 1 # Correction factor

# Slope and intercepts from line of best fit for P vs. T from Initialization
'''PLACEHOLDER VALUES'''
r_th = 366.707 # Thermal Resistance (°C/W)
t_0_1 = 13.39797 # Temperature intercept (°C)
r_chuck = 566 # Resistance at chuck temp
t_initialization = 53 # Temperature from end of initialization (°C)
A_log_path = r"C:\Users\caleb\OneDrive\Desktop\Senior Project\TFR-Senior-Project\logs\A_log_2026.03.03_09.54.33.csv" # Defined from initialization

film_thickness = 200 # Film thickness in nm
tcr_chuck = .0061
time_delay = .5 # seconds

mode = 2 # wire
#f.get_TCR(film_thickness) # TCR in K^-1

#endregion

#region --- Setup and Configuration

# Initialize log file, which defines B_log_path, headers, start_func_time
prefix = "B"
B_log_path, headers, start_func_time = f.initialize_log_file(prefix)

resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR' # Fixed resource ID for Keithley 2450
smu, rm = f.initialize_smu(resource_id) # Initializes SMU

f.top_message(B_log_path, "A -- Initialization\n") # Header for .csv file

#endregion

#region --- 6.2.1: Calculate temperature step and staircase temperature limit

t_stair = t_test - f_power * dt
print("Staircase temperature is ", t_stair)

#endregion

#region --- 6.2.2: Instrument range and voltage compliance for staircase, convergence, stress phases

p_test = (t_test - t_0_1) / r_th # Estimated power at target stress temperature
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

        if t_n_1 < t_stair: 
            #region --- 6.2.3.1: Iterative power calculation (staircase)
            t_est = (t_n_1) + dt # Estimate temperature at next step
            print("\nEstimated temperature for next step is ", t_est)

            p_est = (t_est - t_0_1) / r_th # Estimate electrical power necessary to reach t_i
            print("\nEstimated power for next step is ", p_est)

            #endregion
        else:
            #region --- 6.2.3.1: Iterative power calculation (convergence)
            
            dP = ((t_test + B_E) / (2 - t_n_1)) / r_th
            p_est = (dP/f_power) + p_n_1

            t_est = t_0_1 + (r_th * p_est)
            
            #endregion

        #region --- 6.2.3.2: Iterative forcing current calculation
        
        # (c)
        r_est = r_chuck * (1 + tcr_chuck * ((t_est / F_corr) - t_chuck)) # Estimated resistance at target stress temperature
        
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
        t_n = t_chuck + ((r_n - r_chuck)/(r_chuck * tcr_chuck))
        
        # (g) Obtain new value for thermal resistance and intercept
        r_th, t_0_1, R_squared = g.B_analyze_power_vs_temp(t_n, A_log_path, B_log_path)
        

        print(f"[{n}] I: {i_n:.4f} A | R: {r_n:.4f} Ω | P: {p_n:.2f} W | ΔT: {t_n - t_chuck:.2f} °C")
        f.printcsv(B_log_path, start_func_time, n, i_n * 1000, r_n, p_n, t_n, t_n - t_chuck)

        # Save data point
        results.append({'n': n, 'I': i_n, 'R': r_n, 'P': p_n, 'T': t_n})

        #endregion

        #region --- 6.2.4: Temporary failure criteria for staircase and convergence phases

        r_fail = r_est * (100 + 20)/100

        r_absfail = (abs(r_n - r_est) / min(r_n, r_est))
        if r_absfail >= 20:
            print("you done fucked up")
        
        #endregion
        
        # --- Exit Condition Logic ---
        # Flowchart requires: T_n >= (T_test)
        if t_n >= t_test:
            print(f"\nTarget temperature {t_test} met.")
            print(f"Temperature Staircase loop finished with {n} loops completed.")
            break

        # Set arbitrary delay
        time.sleep(time_delay)

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