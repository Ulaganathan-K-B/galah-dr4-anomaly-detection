"""
from astropy.io import fits
import glob

# We will search for the specific FITS file for your first star in the 'com' folder
sobject_id = "1312160011010021"
date_folder = sobject_id[:6]  # Gets "170910"

# Adjust the path if your 'galah' folder is located somewhere else!
search_path = f"galah/dr4/spectra/hermes/com/{date_folder}/*{sobject_id}*.fits"

found_files = glob.glob(search_path)

if not found_files:
    print(f"Could not find a FITS file for {sobject_id} in {search_path}")
else:
    print(f"Found {len(found_files)} file(s). Looking inside the first one: {found_files[0]}\n")

    # Open the FITS file and print its structure
    hdul = fits.open(found_files[0])
    hdul.info()

    # Let's also look at the column names if it's a table
    for i, hdu in enumerate(hdul):
        if isinstance(hdu, fits.BinTableHDU):
            print(f"\nColumns in Extension {i} ({hdu.name}):")
            print(hdu.columns.names)

    hdul.close()
"""

"""
from astropy.table import Table

catalog = Table.read("galah_dr4_allspec_240705.fits")
# Print all columns that contain 'rv' or 'rad'
rv_cols = [col for col in catalog.colnames if 'rv' in col.lower() or 'rad' in col.lower()]
print("Possible RV columns:", rv_cols)
"""

import matplotlib.pyplot as plt
import pandas as pd

# 1. Extracted data from Output.txt
data = [
    # Gaussian
    {'dist': 'Gaussian', 'nu': 0.5, 'perp': 10.0, 'trust': 0.7398, 'sil': -0.1191},
    {'dist': 'Gaussian', 'nu': 0.5, 'perp': 20.0, 'trust': 0.8003, 'sil': -0.0768},
    {'dist': 'Gaussian', 'nu': 0.5, 'perp': 30.0, 'trust': 0.7948, 'sil': -0.0645},
    {'dist': 'Gaussian', 'nu': 0.5, 'perp': 50.0, 'trust': 0.7972, 'sil': -0.0650},
    {'dist': 'Gaussian', 'nu': 1.0, 'perp': 10.0, 'trust': 0.7443, 'sil': -0.1130},
    {'dist': 'Gaussian', 'nu': 1.0, 'perp': 20.0, 'trust': 0.8007, 'sil': -0.0759},
    {'dist': 'Gaussian', 'nu': 1.0, 'perp': 30.0, 'trust': 0.7936, 'sil': -0.0733},
    {'dist': 'Gaussian', 'nu': 1.0, 'perp': 50.0, 'trust': 0.7994, 'sil': -0.1316},
    {'dist': 'Gaussian', 'nu': 2.0, 'perp': 10.0, 'trust': 0.7451, 'sil': -0.1203},
    {'dist': 'Gaussian', 'nu': 2.0, 'perp': 20.0, 'trust': 0.7995, 'sil': -0.0878},
    {'dist': 'Gaussian', 'nu': 2.0, 'perp': 30.0, 'trust': 0.7955, 'sil': -0.0662},
    {'dist': 'Gaussian', 'nu': 2.0, 'perp': 50.0, 'trust': 0.8003, 'sil': -0.1283},

    # Logistic
    {'dist': 'Logistic', 'nu': 0.5, 'perp': 10.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 0.5, 'perp': 20.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 0.5, 'perp': 30.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 0.5, 'perp': 50.0, 'trust': 0.7414, 'sil': 0.0170},
    {'dist': 'Logistic', 'nu': 1.0, 'perp': 10.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 1.0, 'perp': 20.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 1.0, 'perp': 30.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 1.0, 'perp': 50.0, 'trust': 0.7414, 'sil': 0.0170},
    {'dist': 'Logistic', 'nu': 2.0, 'perp': 10.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 2.0, 'perp': 20.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 2.0, 'perp': 30.0, 'trust': 0.7414, 'sil': 0.0169},
    {'dist': 'Logistic', 'nu': 2.0, 'perp': 50.0, 'trust': 0.7414, 'sil': 0.0170},

    # Power-law
    {'dist': 'Power-law', 'nu': 0.5, 'perp': 10.0, 'trust': 0.9729, 'sil': 0.2235},
    {'dist': 'Power-law', 'nu': 0.5, 'perp': 20.0, 'trust': 0.9746, 'sil': 0.2643},
    {'dist': 'Power-law', 'nu': 0.5, 'perp': 30.0, 'trust': 0.9761, 'sil': 0.2816},
    {'dist': 'Power-law', 'nu': 0.5, 'perp': 50.0, 'trust': 0.9771, 'sil': 0.2917},
    {'dist': 'Power-law', 'nu': 1.0, 'perp': 10.0, 'trust': 0.9678, 'sil': 0.1889},
    {'dist': 'Power-law', 'nu': 1.0, 'perp': 20.0, 'trust': 0.9718, 'sil': 0.2125},
    {'dist': 'Power-law', 'nu': 1.0, 'perp': 30.0, 'trust': 0.9720, 'sil': 0.2221},
    {'dist': 'Power-law', 'nu': 1.0, 'perp': 50.0, 'trust': 0.9701, 'sil': 0.2314},
    {'dist': 'Power-law', 'nu': 2.0, 'perp': 10.0, 'trust': 0.5035, 'sil': -0.1649},
    {'dist': 'Power-law', 'nu': 2.0, 'perp': 20.0, 'trust': 0.5006, 'sil': -0.1252},
    {'dist': 'Power-law', 'nu': 2.0, 'perp': 30.0, 'trust': 0.5023, 'sil': -0.1193},
    {'dist': 'Power-law', 'nu': 2.0, 'perp': 50.0, 'trust': 0.9612, 'sil': 0.2211},

    # T-distribution
    {'dist': 'T-distribution', 'nu': 0.5, 'perp': 10.0, 'trust': 0.9690, 'sil': 0.1845},
    {'dist': 'T-distribution', 'nu': 0.5, 'perp': 20.0, 'trust': 0.9740, 'sil': 0.2335},
    {'dist': 'T-distribution', 'nu': 0.5, 'perp': 30.0, 'trust': 0.9750, 'sil': 0.2465},
    {'dist': 'T-distribution', 'nu': 0.5, 'perp': 50.0, 'trust': 0.9750, 'sil': 0.2585},
    {'dist': 'T-distribution', 'nu': 1.0, 'perp': 10.0, 'trust': 0.9679, 'sil': 0.1895},
    {'dist': 'T-distribution', 'nu': 1.0, 'perp': 20.0, 'trust': 0.9719, 'sil': 0.2125},
    {'dist': 'T-distribution', 'nu': 1.0, 'perp': 30.0, 'trust': 0.9729, 'sil': 0.2225},
    {'dist': 'T-distribution', 'nu': 1.0, 'perp': 50.0, 'trust': 0.9709, 'sil': 0.2315},
    {'dist': 'T-distribution', 'nu': 2.0, 'perp': 10.0, 'trust': 0.9609, 'sil': 0.1797},
    {'dist': 'T-distribution', 'nu': 2.0, 'perp': 20.0, 'trust': 0.9649, 'sil': 0.1887},
    {'dist': 'T-distribution', 'nu': 2.0, 'perp': 30.0, 'trust': 0.9659, 'sil': 0.1937},
    {'dist': 'T-distribution', 'nu': 2.0, 'perp': 50.0, 'trust': 0.9669, 'sil': 0.1937},
]

# 2. Convert to Pandas DataFrame for easy filtering
df = pd.DataFrame(data)

distributions = ['Gaussian', 'Logistic', 'Power-law', 'T-distribution']
nu_values = [0.5, 1.0, 2.0]
markers = ['o', 's', '^', 'D']

# ==========================================
# Plot Set 1: Trustworthiness vs Perplexity
# ==========================================
for nu in nu_values:
    plt.figure(figsize=(8, 5))
    subset_nu = df[df['nu'] == nu]

    for dist, marker in zip(distributions, markers):
        subset_dist = subset_nu[subset_nu['dist'] == dist]
        plt.plot(subset_dist['perp'], subset_dist['trust'],
                 marker=marker, linewidth=2, label=dist)

    plt.title(f'Trustworthiness vs. Perplexity (nu = {nu})', fontsize=14)
    plt.xlabel('Perplexity', fontsize=12)
    plt.ylabel('Trustworthiness Score', fontsize=12)
    plt.xticks([10, 20, 30, 50])
    plt.legend(title="Distributions")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# ==========================================
# Plot Set 2: Silhouette vs Perplexity
# ==========================================
for nu in nu_values:
    plt.figure(figsize=(8, 5))
    subset_nu = df[df['nu'] == nu]

    for dist, marker in zip(distributions, markers):
        subset_dist = subset_nu[subset_nu['dist'] == dist]
        plt.plot(subset_dist['perp'], subset_dist['sil'],
                 marker=marker, linewidth=2, label=dist)

    plt.title(f'Silhouette Score vs. Perplexity (nu = {nu})', fontsize=14)
    plt.xlabel('Perplexity', fontsize=12)
    plt.ylabel('Silhouette Score', fontsize=12)
    plt.xticks([10, 20, 30, 50])
    plt.legend(title="Distributions")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()