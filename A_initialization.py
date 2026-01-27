import functions as f
import sys
import time

# --- Setup Connection ---
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)

# Configure for Current Sourcing and 4-Wire Resistance
# Note: Ensure your library has a function for smu.FUNC_DC_CURRENT
f.config_4wire_resistance_mode(smu, v_limit=1) 

try:
    # --- 6.1.1 & 6.1.3: User Inputs ---
    print("--- JESD33B Initial Parameters ---")
    t_chuck = 20 # Chuck Temperature (°C)
    i_initial = 65 / 1000 # Initial Current I1 (Amps)
    f_current = 1.28 # Current Multiplier
    
    film_thickness = 200 # Film thickness in nm
    tcr_ref = f.get_TCR(film_thickness) # TCR in K^-1

    # 6.1.1: Measure initial resistance (R_chuck) at a very low current
    # We use a low current (e.g., 100uA) to prevent self-heating during the baseline
    print("\nMeasuring baseline R_chuck...")
    r_chuck = f.measure_resistance(smu, 1e-4) 
    print(f"R_chuck measured: {r_chuck:.4f} Ω")

    # --- 6.1.4: Initialization ---
    i = 1
    current_i = i_initial
    r_fail_init = r_chuck + (1 + (tcr_ref * 50))
    
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
        t_i = t_chuck + ((r_i - r_chuck) / (r_chuck * tcr_ref))
        
        print(f"[{i}] I: {current_i:.4e} A | R: {r_i:.4f} Ω | ΔT: {t_i - t_chuck:.2f} °C")

        # 6.1.6: Check for failure
        if r_i >= r_fail_init:
            print("!! FAILURE DETECTED: Resistance limit exceeded. Exiting.")
            break

        # Save data point
        results.append({'i': i, 'I': current_i, 'R': r_i, 'P': p_i, 'T': t_i})

        # --- Exit Condition Logic ---
        # Flowchart requires: T_i >= (T_chuck + 50) AND i >= 5
        if t_i >= (t_chuck + 50) and i >= 5:
            print("\nTarget temperature (+50°C) and iteration count (>=5) met.")
            break
        
        # Increment for next iteration
        current_i *= f_current
        i += 1

    # 6.1.7: Proceed to Determination of Rth
    print(f"\nLoop Finished. Collected {len(results)} data points.")

finally:
    # Safety: Always turn off output and close connection
    smu.write("smu.source.output = smu.OFF")
    smu.close()
    rm.close()
    print("Instrument safely disconnected.")