import Functions as f
import time
import math
import json
import sys

# ==========================================
# CONFIGURATION (JESD61A SECTION 6.2)
# ==========================================
TARGET_TEMP = 325.0       # Final Stress Temperature (°C)
STEP_SIZE   = 50.0        # Temperature Step Size (°C) - (Sec 6.2.1)
TEMP_TOLERANCE = 1.0      # Convergence Error Band (+/- °C) - (Sec 3.6)
SETTLE_TIME = 2.0         # Seconds to wait at each step for stability
FAIL_INCREASE = 0.10      # 10% R increase limit during warm-up (Sec 6.2.4)

# Load Initialization Parameters
try:
    with open("init_params.json", "r") as infile:
        data = json.load(infile)
        R_REF = data["r_ref"]
        R_TH_INIT = data["r_th"] # Initial R_th from Phase 1
        TCR = data["tcr"]
        T_CHUCK = data["t_chuck"]
        print(f"Loaded: R_ref={R_REF:.4f} | R_th_init={R_TH_INIT:.2f} | TCR={TCR:.6f}")
except FileNotFoundError:
    print("CRITICAL ERROR: 'init_params.json' not found. Run Initialization.py first.")
    sys.exit()

# Setup Connection
resource_id = 'USB0::0x05E6::0x2450::04419551::INSTR'
smu, rm = f.initialize_smu(resource_id)
f.config_4wire_current_source(smu, v_limit=20) # Higher compliance for high temp

def get_temp(r_now):
    """Calculates T_line using the Joule Heating TCR equation"""
    # T = T_chuck + (R - R_ref) / (R_ref * TCR)
    return T_CHUCK + ((r_now - R_REF) / (R_REF * TCR))

try:
    print(f"\n--- PHASE 2: TEMPERATURE STAIRCASE (Target: {TARGET_TEMP}°C) ---")
    
    current_temp_goal = T_CHUCK
    current_I = 0.001 # Start low
    
    # We maintain a running estimate of R_th because it changes with Temperature
    R_th_current = R_TH_INIT 
    
    # 6.2.1: Determine Staircase Steps
    # We loop until we are close to the target
    while current_temp_goal < TARGET_TEMP:
        
        # Increment Target (don't exceed final target)
        current_temp_goal += STEP_SIZE
        if current_temp_goal > TARGET_TEMP:
            current_temp_goal = TARGET_TEMP
            
        print(f"\n>> Ramping to Step: {current_temp_goal:.1f} °C")
        
        # --- CONTROL LOOP FOR THIS STEP (Sec 6.2.3) ---
        # We iterate until T is within tolerance of current_temp_goal
        while True:
            # 1. Measure State
            v, i_meas, r_now = f.measure_vals(smu, current_I)
            t_now = get_temp(r_now)
            p_now = v * i_meas
            
            # 2. Check Safety (Sec 6.2.4)
            # If R increases significantly > predicted thermal rise, it's damage.
            # Simplified check: R shouldn't be drastically higher than expected for this Temp.
            # (Strict JESD61A check requires calculating 'R_fail_step')
            if r_now > R_REF * 2.0: 
                raise Exception("FAIL: Resistance doubled. Line broke during ramp.")

            print(f"   Meas: T={t_now:.1f}C | R={r_now:.4f} | P={p_now*1000:.1f}mW")

            # 3. Check Convergence for this Step
            if abs(t_now - current_temp_goal) < TEMP_TOLERANCE:
                # We reached this step. Update R_th estimate for next step accuracy.
                # R_th_new = (T_now - T_chuck) / P_now
                # This accounts for the non-linearity of R_th at high temps.
                if p_now > 0:
                    R_th_current = (t_now - T_CHUCK) / p_now
                
                print(f"   -> Step Reached. Updated R_th: {R_th_current:.2f} C/W")
                time.sleep(SETTLE_TIME) # Wait for thermal equilibrium
                break 
            
            # 4. Calculate Next Current (Isothermal Feedback)
            # Power needed for Goal: P_req = (T_goal - T_chuck) / R_th_current
            # Current needed: I = sqrt( P_req / R_now )
            
            # Note: We use the *updated* R_th_current if we have one, or the initial.
            p_required = (current_temp_goal - T_CHUCK) / R_th_current
            
            if p_required < 0: p_required = 0.001 # Safety
            
            # Predictive Current Calculation
            new_I = math.sqrt(p_required / r_now)
            
            # 5. Damping / Safety Limits
            # Don't let current jump more than 10% in one cycle to prevent oscillation
            if new_I > current_I * 1.10: new_I = current_I * 1.10
            if new_I < current_I * 0.90: new_I = current_I * 0.90
            
            # Apply
            current_I = new_I
            # Small delay for hardware to settle
            time.sleep(0.1)

    print("\n--- PHASE 2 COMPLETE: TARGET TEMPERATURE REACHED ---")
    print(f"Final State: T={t_now:.1f}C, I={current_I:.4f}A, R={r_now:.4f}Ω")

    # ==========================================
    # SAVE STATE FOR STRESS TEST
    # ==========================================
    # The Stress Test needs to know exactly what Current/Power maintains 325C
    stress_params = {
        "target_temp": TARGET_TEMP,
        "start_current": current_I,
        "target_power": p_now,     # This is P_test
        "final_r": r_now,          # Resistance at start of stress
        "r_ref": R_REF,
        "tcr": TCR,
        "t_chuck": T_CHUCK
    }
    
    with open("stress_params.json", "w") as outfile:
        json.dump(stress_params, outfile)
    print("Params saved to 'stress_params.json'. Ready for Stress_Test.py")

except Exception as e:
    print(f"\nERROR: {e}")
    smu.write("smu.source.output = smu.OFF")

finally:
    # NOTE: We do NOT turn off the output if we are moving immediately to stress.
    # However, since this is a separate file, we must turn it off.
    # *CRITICAL*: In a real setup, these scripts should be combined or the
    # instrument state preserved. If you turn off output now, the line cools down.
    # For this modular file approach:
    print("Keeping Output ON for 5 seconds to demonstrate stability, then OFF.")
    time.sleep(5)
    smu.write("smu.source.output = smu.OFF")
    smu.close()
    rm.close()
