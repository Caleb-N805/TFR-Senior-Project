import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def analyze_power_vs_temp(csv_path):
    # Analyzes Power vs Temperature for rows where the change in temperature is > 0.
    # Returns slope, y-intercept, and R^2 value.
    
    # Read the CSV file, skipping the first 'Initialization' row
    df = pd.read_csv(csv_path, skiprows=1)
    df.columns = [col.strip() for col in df.columns]

    # Identify relevant columns (handling potential character encoding/typos)
    col_change_t = 'Change in Temperature (C)'
    col_power = 'Power (W)'
    # Find the temperature column (it might contain a copyright symbol or similar)
    col_temp = [c for c in df.columns if 'Temperature' in c and 'Change' not in c][0]

    # Filter data where change in temperature is greater than 0
    filtered_df = df[df[col_change_t] > 0].copy()

    x = filtered_df[col_power]
    y = filtered_df[col_temp]

    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_squared = r_value**2

    '''
    #region --- Plot, optional

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, label='Experimental Data', color='blue', alpha=0.5)
    
    # Line of best fit
    fit_line = slope * x + intercept
    plt.plot(x, fit_line, color='red', 
             label=f'Linear Fit: $y = {slope:.4f}x + {intercept:.4f}$')

    plt.xlabel('Power (W)')
    plt.ylabel('Temperature (C)')
    plt.title('Power (W) vs. Temperature (C) (Filtered for dT > 0)')
    plt.legend()
    plt.grid(True)
    plt.savefig('power_vs_temp_plot.png')

    #endregion
    '''

    return slope, intercept, r_squared