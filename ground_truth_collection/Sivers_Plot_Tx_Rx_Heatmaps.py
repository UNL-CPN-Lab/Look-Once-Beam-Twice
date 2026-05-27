"""TX × RX SNR heatmap for ground-truth sweep data.

Reads the per-pair CSV / per-`tx_beam` `.dat` buffers written by the rotor-driven
sweep scripts and renders a 64 × 64 heatmap PNG annotated with the best beam
pair. Imported as `heatmap` by `BeamSweeponRotor.py` and similar scripts.

Author: Apala Pramanik
"""

from matplotlib.colors import LinearSegmentedColormap, BoundaryNorm
import numpy as np
import seaborn as sns # type: ignore
import matplotlib.pyplot as plt
import pandas as pd # type: ignore
from matplotlib.patches import Rectangle
import os
from datetime import datetime
from configurations.utils import *
from configurations.config import *


# Render the TX × RX SNR heatmap for a sweep directory and save it as
# `<basename>_heatmap.png` alongside a `max_signal_powers_RFM06010.csv` table.
def plotheatmap(sweep_directory_path,samples_per_beam):

    # Extract folder name to use as the plot filename
    folder_name = os.path.basename(os.path.normpath(sweep_directory_path))
    plot_filename = os.path.join(sweep_directory_path, f"{folder_name}_heatmap.png")


    # Define the number of beams and samples per beam
    num_beams = 63
    
    rx_beam_angles = [-45.0, -43.5, -42.1, -40.6, -39.2, -37.7, -36.3, -34.8, -33.4, -31.9, -30.5, -29.0, -27.6, -26.1, -24.7, -23.2, -21.8, -20.3, -18.9, -17.4, -16.0, -14.5, -13.1, -11.6, -10.2, -8.7, -7.3, -5.8, -4.4, -2.9, -1.5, 0, 1.5, 2.9, 4.4, 5.8, 7.3, 8.7, 10.2, 11.6, 13.1, 14.5, 16.0, 17.4, 18.9, 20.3, 21.8, 23.2, 24.7, 26.1, 27.6, 29.0, 30.5, 31.9, 33.4, 34.8, 36.3, 37.7, 39.2, 40.6, 42.1, 43.5, 45.0]
    
    beam_angles = [45.0, 43.5, 42.1, 40.6, 39.2, 37.7, 36.3, 34.8, 33.4, 31.9, 30.5, 29.0, 27.6, 26.1, 24.7, 23.2, 21.8, 20.3, 18.9, 17.4, 16.0, 14.5, 13.1, 11.6, 10.2, 8.7, 7.3, 5.8, 4.4, 2.9, 1.5, 0, -1.5, -2.9, -4.4, -5.8, -7.3, -8.7, -10.2, -11.6, -13.1, -14.5, -16.0, -17.4, -18.9, -20.3, -21.8, -23.2, -24.7, -26.1, -27.6, -29.0, -30.5, -31.9, -33.4, -34.8, -36.3, -37.7, -39.2, -40.6, -42.1,-43.5, -45.0]

    # Initialize arrays to store the signal strength and power
    signal_strength = np.full((num_beams, num_beams), -100, dtype=float) 
    avg_signal_powers = np.full((num_beams, num_beams), -100, dtype=float) 
    max_signal_powers = np.full((num_beams, num_beams), -100, dtype=float) 
    
    for tx_beam in range(num_beams):
        mean_strengths, avg_powers_in_dBm, max_powers_in_dBm = [], [], []
        # filename = os.path.join(sweep_directory_path, f'tx_beam_{tx_beam}.dat')
        filename = os.path.join(sweep_directory_path, "tx_beam_{}.dat".format(tx_beam))

        if os.path.exists(filename) and os.path.getsize(filename) > 0:
            with open(filename, 'rb') as f:
                for rx_beam in range(num_beams):
                    data_array = np.fromfile(f, dtype=np.complex64, count=samples_per_beam)
                    print("Data array shape = ",data_array.shape)
                    if data_array.size == 0:
                        mean_strengths.append(np.nan)
                        avg_powers_in_dBm.append(np.nan)
                        max_powers_in_dBm.append(np.nan)
                        continue

                    IQ_power_dBm, avg_power_dBm, max_power_dBm = calculate_power_metrics(data_array)
                    mean_strengths.append(round(np.mean(np.abs(data_array)), 4))
                    avg_powers_in_dBm.append(round(avg_power_dBm, 2))
                    max_powers_in_dBm.append(round(max_power_dBm, 2))

        else:
            mean_strengths = [np.nan] * num_beams
            avg_powers_in_dBm = [np.nan] * num_beams
            max_powers_in_dBm = [np.nan] * num_beams

        signal_strength[tx_beam, :] = mean_strengths
        avg_signal_powers[tx_beam, :] = avg_powers_in_dBm
        max_signal_powers[tx_beam, :] = max_powers_in_dBm

    # Find the index of the maximum value in the signal_strength array
    index_max = np.argmax(max_signal_powers)

    # Convert the flat index to a 2D index (row, column)
    tx_index, rx_index = np.unravel_index(index_max, max_signal_powers.shape)

    center_power = max_signal_powers[31,31]

    # After finding the indices of the maximum value
    max_signal_power = max_signal_powers[tx_index, rx_index]

    # Extract the corresponding beam angles using the indices
    tx_beam_angle_max = beam_angles[tx_index]
    rx_beam_angle_max = rx_beam_angles[rx_index]

    print(f"Maximum signal strength of {max_signal_power} dBm ; Center power of {center_power} dBm")


    '''
    Save the recieved powers to a CSV file and plot the heatmap
    '''
    # Prepare the data
    # Create a DataFrame from the max_signal_powers array
    df = pd.DataFrame(max_signal_powers)

    # Add Tx and Rx beam angles as the index and column names
    df.index = beam_angles  # Assuming beam_angles is a list of Tx beam angles
    df.columns = rx_beam_angles  # Assuming the same angles are used for Rx

    # Optionally, if you want to "melt" the DataFrame to have a long-form DataFrame with Tx, Rx, and Power columns, you can do:
    df_melted = df.reset_index().melt(id_vars='index', var_name='Rx', value_name='Power')
    df_melted.rename(columns={'index': 'Tx'}, inplace=True)

    csv_filename = os.path.join(sweep_directory_path, "max_signal_powers_RFM06010.csv")
    # Save to CSV
    df.to_csv(csv_filename, index=True) # Save the original matrix form
    
    '''
    Plot the heatmap
    '''
    # Define the Tx and Rx beam angles
    tx_angles = beam_angles
    rx_angles = rx_beam_angles


    # Custom colormap from black (lowest power) to blue (medium power) to red (highest power)
    colors = ["black", "blue", "red"]  # Black to Blue to Red
    n_bins = 10000  # Use 10000 bins to make the transition smooth
    cmap_name = "custom_black_blue_red"
    custom_black_blue_red = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)

    sns.set()  # Set the default Seaborn style
    plt.figure(figsize=(20,10))  # Adjust the figure size

    # Plot the heatmap with the custom black-to-blue-to-red colormap
    ax = sns.heatmap(max_signal_powers, cmap=custom_black_blue_red, vmin=-60, vmax=-40, cbar_kws={'label': 'Rx Power(dBm)', 'pad': 0.02})


    # Increase the font size of the colorbar label
    cbar = ax.collections[0].colorbar
    cbar.ax.yaxis.label.set_size(20)

    # Increase the font size of the colorbar tick labels
    cbar.ax.tick_params(labelsize=20)  # Adjust the value as needed

    # Define the range of ticks
    ticks = np.arange(-45, 50, 5)  # Include 45

    # Set x and y ticks to show multiples of 5 from -45 to 45 for Rx and 45 to -45 for Tx, and rotate x-ticks
    ax.set_xticks(np.linspace(0, len(rx_angles) - 1, len(ticks)))
    ax.set_yticks(np.linspace(0, len(tx_angles) - 1, len(ticks)))
    ax.set_xticklabels(ticks, fontsize=20, rotation=45,fontweight='bold')
    ax.set_yticklabels(ticks[::-1], fontsize=20, rotation=0,fontweight='bold') 

  

    # Add a point where the maximum signal is located
    ax.scatter(rx_index, tx_index, color='white', s=200, linewidth=2)

    # # Add a point at the center
    # ax.scatter(31, 31, color='yellow', s=200, linewidth=2)

    # # Add text at the (0, 0) index
    # ax.text(0.5, 0.5, "(0,0)", color='yellow', fontsize=12, ha='center', va='center')

    plt.xlabel('Rx Beam Angle', fontsize=20,fontweight='bold')
    plt.ylabel('Tx Beam Angle', fontsize=20,fontweight='bold')
    max_signal_power=round(max_signal_power,2)
    center_power = round(center_power,2)
    # plt.title(f"Maximum signal strength : {max_signal_power} dBm ; Center power :{center_power} dBm at {distance}m and {elevation}ft height ", fontsize=20, fontweight = 'bold')
    plt.tight_layout()  # To ensure everything fits nicely
   

    # Save the plot to a file
    plt.savefig(plot_filename, dpi=500, bbox_inches='tight')
    
    # Disable plot to let the function be used in a loop
    plt.show()


# # Example Usage:
# sweep_directory_path = "<DATA_ROOT>/mmWaveSSD/Schorr_Center/Full_Sweep_Experiment/sweepData/s_jun9_gain15db_3m_t1" # linux
# # sweep_directory_path = "sweepData/test_apr3" # linux
# plotheatmap(sweep_directory_path,2000) 