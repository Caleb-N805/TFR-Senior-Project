from A_initialization_alpha import initialization
import csv
import numpy as np

# Define the filename
filename = "tfr_data_log.csv"

# Open the file in write mode
with open(filename, mode='w', newline='') as csvfile:
    # Define the headers
    fieldnames = ['f_current', 'time_delay', 'i', 'R_th', 'T_0_1']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # Write the header row
    writer.writeheader()

    for i in range(8):
        f_current = 1.01 + (i * 0.005) # f_current ranges from 1.01 to 1.05
        for j in range(11):
            time_delay = 0.25 + (j * 0.25) # time_delay ranges from 0.25s to 3s

            i, R_th, T_0_1 = initialization(f_current, time_delay) # Run full initialization script

            # Log the data for the current iteration
            writer.writerow({
                'f_current': round(f_current, 4),
                'time_delay': round(time_delay, 2),
                'i': i,
                'R_th': round(R_th, 2),
                'T_0_1': round(T_0_1, 4),
            })

        print(f"Data successfully logged to {filename} for f_current = {f_current} and time_delay = {time_delay}\n")