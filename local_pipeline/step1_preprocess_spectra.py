# step1_preprocess_spectra.py
import numpy as np
from scipy.interpolate import interp1d
from astropy.io import fits
from astropy.table import Table
import glob
import os


def main():
    catalog_file = "galah_dr4_allspec_240705.fits"
    spectra_path = "galah/dr4/spectra/hermes/com/*/*.fits"

    print("Loading GALAH catalog...")
    catalog = Table.read(catalog_file)

    rv_col_name = 'rv_comp_1'
    print(f"Using '{rv_col_name}' for Radial Velocity.")

    # Create a fast lookup dictionary (WITH BULLETPROOF STRING HANDLING)
    catalog_dict = {}
    for row in catalog:
        raw_id = row['sobject_id']

        # Safely convert to a clean string
        if isinstance(raw_id, bytes):
            sid = raw_id.decode('utf-8').strip()
        elif isinstance(raw_id, (float, np.floating)):
            sid = str(int(raw_id))
        else:
            sid = str(raw_id).strip()

        rv = row[rv_col_name] if not np.isnan(row[rv_col_name]) else 0.0
        ra = row['ra']
        dec = row['dec']
        catalog_dict[sid] = (rv, ra, dec)

    uniform_grid = np.linspace(4700, 7900, 4096)

    processed_spectra = []
    processed_ids = []
    processed_radec = []

    files = glob.glob(spectra_path)
    print(f"Found {len(files)} FITS files. Processing...")

    c = 299792.458  # Speed of light in km/s
    last_seen_id = None

    for file in files:
        filename = os.path.basename(file)

        # --- THE FIX IS HERE ---
        # Strip '.fits', remove whitespace, and KEEP ONLY THE FIRST 15 DIGITS
        sobject_id = filename.split('_')[0].replace('.fits', '').strip()[:15]
        last_seen_id = sobject_id

        if sobject_id not in catalog_dict:
            continue

        rv, ra, dec = catalog_dict[sobject_id]

        try:
            with fits.open(file) as hdul:
                header = hdul[0].header

                try:
                    flux = hdul[1].data
                except IndexError:
                    flux = hdul[0].data

                crval = header['CRVAL1']
                cdelt = header['CDELT1']
                crpix = header.get('CRPIX1', 1)

                pixels = np.arange(header['NAXIS1']) + 1
                wavelengths = crval + (pixels - crpix) * cdelt

                # De-redshift
                z = rv / c
                rest_wavelengths = wavelengths / (1 + z)

                # Interpolate
                interpolator = interp1d(rest_wavelengths, flux, bounds_error=False, fill_value=np.nan)
                regridded_flux = interpolator(uniform_grid)

                # Clean up NaNs
                regridded_flux = np.nan_to_num(regridded_flux, nan=1.0)

                processed_spectra.append(regridded_flux)
                processed_ids.append(sobject_id)
                processed_radec.append([ra, dec])

        except Exception as e:
            print(f"Skipped {filename}: {e}")

    # DEBUG CATCHER
    if not processed_spectra:
        print("\n--- DEBUG INFO ---")
        print("No spectra were processed! The IDs are still mismatching.")
        print(f"Here is an ID from your files: '{last_seen_id}'")
        sample_keys = list(catalog_dict.keys())[:5]
        print(f"Here are IDs from the catalog: {sample_keys}")
        print("Look closely at the differences above (extra spaces, quotes, etc).")
        return

    X = np.array(processed_spectra)
    np.save("b2_uniform_spectra.npy", X)
    np.save("b2_processed_ids.npy", np.array(processed_ids))
    np.save("b2_processed_radec.npy", np.array(processed_radec))
    print(f"\nSuccessfully processed {X.shape[0]} spectra!")


if __name__ == "__main__":
    main()