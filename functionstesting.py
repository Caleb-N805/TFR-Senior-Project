import pyvisa
import time
import csv
from datetime import datetime
from pathlib import Path

# Variables
log_folder = Path("logs")
start_func_time = time.perf_counter()
session_start = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
log_folder.mkdir(parents=True, exist_ok=True)
log_file = log_folder / f"log_{session_start}.csv"
headers = ["Date", "Time Elapsed", "Iteration #", "Current (mA)", "Resistance (Ω)", "Change in Temperature (°C)"]

def initialize_smu(resource_id):
    """Connects to the instrument and performs a basic reset."""
    rm = pyvisa.ResourceManager()
    instrument = rm.open_resource(resource_id)
    instrument.timeout = 5000
    
    # TSP reset command
    instrument.write("reset()")
    return instrument, rm

def config_2wire_resistance_mode(instrument, vlimit):
    """Sets up 2-wire sense for current sourcing."""
    # Set to Current Source
    instrument.write("smu.source.func = smu.FUNC_DC_CURRENT")
    
    # Set to 2-Wire Sense
    # This matches your physical 2-wire connection
    instrument.write("smu.measure.sense = smu.SENSE_2WIRE")
    
    # Set Voltage Limit (Compliance)
    instrument.write(f"smu.source.vlimit.level = {vlimit}")
    print("TSP: 2-Wire Source Configured.")

def config_4wire_resistance_mode(instrument, vlimit):
    """Sets up 4-wire sense for current sourcing."""
    # Set to Current Source
    instrument.write("smu.source.func = smu.FUNC_DC_CURRENT")
    # Set to 4-Wire Sense
    instrument.write("smu.measure.sense = smu.SENSE_4WIRE")
    # Set Current Limit (Compliance)
    instrument.write(f"smu.source.vlimit.level = {vlimit}")
    print("TSP: 4-Wire Source Configured.")

def get_TCR(thickness):
    """Finds TCR based on thin film thickness in nm"""
    TCR_table = {
        200:0.00336,
        100:0.00329,
        85:0.00327,
        60:0.00325,
        40:0.00323,
        20:0.00307
    }
    
    # Use .get() to avoid crashing if the key doesn't exist
    TCR = TCR_table.get(thickness)
    
    if TCR is not None:
        return TCR
    else:
        return "Error: Input not found in table"
    
def measure_resistance_2wire(instrument, current_level):
    """Sets current, measures voltage, and returns calculated resistance."""
    # 1. Set the source level
    instrument.write(f"smu.source.level = {current_level}")
    
    # 2. Ensure SMU is measuring Voltage
    instrument.write("smu.measure.func = smu.FUNC_DC_VOLTAGE")
    
    # 3. Turn on the output
    instrument.write("smu.source.output = smu.ON")
    
    # 4. Query the voltage measurement
    v_measured = instrument.query("print(smu.measure.read())")
    v_float = float(v_measured.strip())
    
    # 5. Calculate Resistance (R = V / I)
    calculated_r = v_float / current_level
    
    return calculated_r

def measure_resistance_4wire(instrument, current_level):
    """Sets current, measures voltage using 4-wire sense, and returns resistance."""
    # 1. Set the source level
    instrument.write(f"smu.source.level = {current_level}")
    
    # 2. Set measurement function to Voltage
    instrument.write("smu.measure.func = smu.FUNC_DC_VOLTAGE")

    # --- NEW: Enable 4-Wire (Remote) Sensing ---
    # This tells the SMU to use the 'Sense' terminals instead of the 'Input' terminals
    instrument.write("smu.measure.sense = smu.SENSE_REMOTE")
    # -------------------------------------------
    
    # 3. Turn on the output
    instrument.write("smu.source.output = smu.ON")
    
    # 4. Query the voltage measurement
    v_measured = instrument.query("print(smu.measure.read())")
    v_float = float(v_measured.strip())
    
    # 5. Calculate Resistance (R = V / I)
    calculated_r = v_float / current_level
    
    # Optional: Turn output off after measurement to be safe
    # instrument.write("smu.source.output = smu.OFF")
    
    return calculated_r

def tprint(string):
    now = datetime.now()
    perf_now = time.perf_counter()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    total_elapsed = perf_now - start_func_time
    hours, rem = divmod(total_elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    elapsed_str = f"{int(hours):02}:{int(minutes):02}:{seconds:06.3f}"
    log_entry = f"[{timestamp_str}] (Total Time Elapsed: {elapsed_str}) - {string}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

def csvheader ():
    with open(log_file, "a", newline = "", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

def printcsv (iteration, current, resistance, temperature):
    with open(log_file, "a", newline = '', encoding = "utf-8") as f:
        writer = csv.writer(f)
        now = datetime.now()
        perf_now = time.perf_counter()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        total_elapsed = perf_now - start_func_time
        hours, rem = divmod(total_elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        elapsed_str = f"{int(hours):02}:{int(minutes):02}:{seconds:06.3f}"
        writer.writerow([timestamp_str, elapsed_str, iteration, f"{current:.3f}", f"{resistance:.3f}", f"{temperature:.3f}"])