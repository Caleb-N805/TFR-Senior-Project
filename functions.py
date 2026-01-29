import pyvisa
import time
from datetime import datetime
from pathlib import Path
log_folder = Path("logs")
start_func_time = time.perf_counter()
session_start = datetime.now().strftime("%Y.%m.%d_%H.%M.%S")
log_folder.mkdir(parents=True, exist_ok=True)
time_file = log_folder / f"log_{session_start}.log"

def initialize_smu(resource_id):
    """Connects to the instrument and performs a basic reset."""
    rm = pyvisa.ResourceManager()
    instrument = rm.open_resource(resource_id)
    instrument.timeout = 5000
    
    # TSP reset command
    instrument.write("reset()")
    return instrument, rm

def config_4wire_resistance_mode(instrument, vlimit=1):
    """Sets up 4-wire sense for current sourcing."""
    # Set to Current Source
    instrument.write("smu.source.func = smu.FUNC_DC_CURRENT")
    # Set to 4-Wire Sense
    instrument.write("smu.measure.sense = smu.SENSE_4WIRE")
    # Set Current Limit (Compliance)
    instrument.write(f"smu.source.ilimit.level = {vlimit}")
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
    
def measure_resistance(instrument, current_level):
    """Sets current, measures resistance, and returns value."""
    instrument.write(f"smu.source.level = {current_level}")
    instrument.write("smu.source.output = smu.ON")
    
    # Query the resistance measure function of the 2450
    # The 2450 can return R directly if smu.measure.func = smu.FUNC_RESISTANCE is set
    res = instrument.query("print(smu.measure.read())")
    
    return float(res.strip())

def tprint (string):
    now = datetime.now()
    perf_now = time.perf_counter()
    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    total_elapsed = perf_now - start_func_time
    hours, rem = divmod(total_elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    elapsed_str = f"{int(hours):02}:{int(minutes):02}:{seconds:06.3f}"
    log_entry = f"[{timestamp_str}] (Total Time Elapsed: {elapsed_str}) - {string}\n"
    with open(time_file, "a") as f:
        f.write(log_entry)
