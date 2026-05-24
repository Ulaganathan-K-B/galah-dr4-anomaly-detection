# =====================================================================
# GALAH DR4 Stellar Anomaly Detection Pipeline (Local/Uploaded Data)
# =====================================================================

# !pip install -q openTSNE astroquery astropy tqdm scikit-learn

import numpy as np
import os
import glob
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.simbad import Simbad
from astroquery.exceptions import NoResultsWarning
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
from openTSNE import TSNE as openTSNE
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from tqdm.notebook import tqdm

warnings.filterwarnings('ignore', category=NoResultsWarning)
warnings.filterwarnings('ignore')

# ===================================================================
# 1. Configuration (Set your paths here!)
# ===================================================================

# ── Paths ─────────────────────────────────────────────────────────────
# CHANGE THIS to match your Kaggle dataset name and folder structure
SPECTRA_DIR   = "/kaggle/input/datasets/ulaganathankb/galah-dataset/com"
CATALOG_PATH  = "/kaggle/input/datasets/ulaganathankb/galah-dr4-catalog/galah_dr4_allspec_240705.fits"
OUTPUT_DIR    = "/kaggle/working"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Pipeline Tuning ───────────────────────────────────────────────────
N_STARS           = None   # Max stars to process
CCD_ARM           = 3        # 1=Blue, 2=Green, 3=Red, 4=IR
N_PCA_COMPONENTS  = 50       
TSNE_PERPLEXITY   = 30       
GLOBAL_EPS        = 3.0      # Tune this! Increase if too many anomalies are found
GLOBAL_MIN_SAMPLES = 50      
LOCAL_EPS         = 2.0      
LOCAL_MIN_SAMPLES = 3        
N_WORKERS         = os.cpu_count() or 4  # Maximize local thread usage

# ── Physics ───────────────────────────────────────────────────────────
SPEED_OF_LIGHT = 299792.458  
UNIFORM_GRID   = np.linspace(4700, 7900, 4096)   

print("Configuration loaded. Using offline data from:", SPECTRA_DIR)


# ===================================================================
# 2. Load Catalog & Map Local Files
# ===================================================================

print("Loading GALAH DR4 allspec catalog...")
catalog = Table.read(CATALOG_PATH)

catalog_dict = {}
for row in catalog:
    raw_id = row['sobject_id']
    sid = str(int(raw_id)) if isinstance(raw_id, (float, np.floating)) else (raw_id.decode().strip() if isinstance(raw_id, bytes) else str(raw_id).strip())

    # Only store the target arm (ensuring the 16th digit is correct)
    if sid.endswith(str(CCD_ARM)):
        rv = float(row['rv_comp_1']) if not np.isnan(row['rv_comp_1']) else 0.0
        catalog_dict[sid] = {'rv': rv, 'ra': float(row['ra']), 'dec': float(row['dec'])}

print(f"Target catalog entries for Arm-{CCD_ARM}: {len(catalog_dict):,}")

# Scan the uploaded directory for FITS files
print(f"Scanning {SPECTRA_DIR} for FITS files...")
all_files = glob.glob(f"{SPECTRA_DIR}/**/*.fits", recursive=True)
print(f"Found {len(all_files):,} total FITS files on disk.")

# Match files to our catalog (ensuring they belong to the correct arm)
matched_files = []
for file_path in all_files:
    # Extract the base 16-digit ID from the filename
    filename = os.path.basename(file_path)
    sid = filename.split('_')[0].replace('.fits', '').strip()
    
    if sid in catalog_dict:
        matched_files.append((sid, file_path))
        if N_STARS is not None and len(matched_files) >= N_STARS:
            break

print(f"Selected {len(matched_files):,} matching files for processing.")


# ===================================================================
# 3. Fast Parallel Preprocessing
# ===================================================================

def process_local_fits(sid, file_path):
    info = catalog_dict[sid]
    try:
        with fits.open(file_path, memmap=True) as hdul:
            header = hdul[0].header
            flux = hdul[1].data.astype(np.float64) if len(hdul) > 1 else hdul[0].data.astype(np.float64)

            if flux is None or flux.ndim == 0 or len(flux) < 10:
                return None

            crval = header['CRVAL1']
            cdelt = header['CDELT1']
            crpix = header.get('CRPIX1', 1)
            wavelengths = crval + (np.arange(header['NAXIS1']) + 1 - crpix) * cdelt

            # De-redshift
            rest_wavelengths = wavelengths / (1.0 + (info['rv'] / SPEED_OF_LIGHT))

            # Interpolate onto uniform grid
            valid = np.isfinite(flux) & (flux > 0)
            if valid.sum() < 10: return None

            regridded = np.interp(UNIFORM_GRID, rest_wavelengths[valid], flux[valid], left=np.nan, right=np.nan)
            regridded = np.nan_to_num(regridded, nan=1.0).astype(np.float32)

            # Median continuum normalisation
            pos_vals = regridded[regridded > 0]
            median = np.median(pos_vals) if len(pos_vals) > 10 else 0
            if not np.isfinite(median) or median <= 0: return None
            
            regridded /= median
            if np.mean(regridded) < 0.05: return None

            return sid, regridded, info['ra'], info['dec']
    except Exception:
        return None

print(f"Preprocessing spectra with {N_WORKERS} threads...")
processed_spectra, processed_ids, processed_radec = [], [], []

with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
    futures = [pool.submit(process_local_fits, sid, path) for sid, path in matched_files]
    for future in tqdm(as_completed(futures), total=len(futures), desc="Processing"):
        res = future.result()
        if res is not None:
            sid, spec, ra, dec = res
            processed_spectra.append(spec)
            processed_ids.append(sid)
            processed_radec.append([ra, dec])

X     = np.array(processed_spectra, dtype=np.float32)
IDs   = np.array(processed_ids)
RADec = np.array(processed_radec, dtype=np.float64)

print(f"\nValid spectra processed: {X.shape[0]:,}")


# ===================================================================
# 4. PCA Reduction
# ===================================================================

n_components = min(N_PCA_COMPONENTS, X.shape[0] - 1)
print(f"Running PCA: {X.shape[1]:,} dims -> {n_components} components...")
pca   = PCA(n_components=n_components, random_state=42)
X_pca = pca.fit_transform(X.astype(np.float64))
print(f"Variance retained: {np.sum(pca.explained_variance_ratio_) * 100:.2f}%")


# ===================================================================
# 5. Global t-SNE & DBSCAN (Normal Star Filter) & Plotting
# ===================================================================

print("\nRunning Barnes-Hut t-SNE (Global)...")
tsne_global = openTSNE(n_components=2, perplexity=TSNE_PERPLEXITY, n_jobs=-1, random_state=42)
Y_global = np.array(tsne_global.fit(X_pca))

dbscan_global = DBSCAN(eps=GLOBAL_EPS, min_samples=GLOBAL_MIN_SAMPLES, n_jobs=-1)
labels_global = dbscan_global.fit_predict(Y_global)

anomaly_mask = (labels_global == -1)
print(f"Normal stars isolated: {(~anomaly_mask).sum():,}")
print(f"Anomaly candidates: {anomaly_mask.sum():,} ({(anomaly_mask.sum()/X.shape[0])*100:.1f}%)")

# --- ADDED: Save Global t-SNE Plot ---
plt.figure(figsize=(10, 8))
plt.scatter(Y_global[~anomaly_mask, 0], Y_global[~anomaly_mask, 1], c='blue', alpha=0.3, s=5, label='Normal Stars')
plt.scatter(Y_global[anomaly_mask, 0], Y_global[anomaly_mask, 1], c='red', alpha=0.8, s=15, label='Anomalies (-1)')
plt.title("Global t-SNE Space (Normal vs. Anomalies)")
plt.xlabel("t-SNE Dimension 1")
plt.ylabel("t-SNE Dimension 2")
plt.legend()
plt.savefig(f"{OUTPUT_DIR}/global_tsne.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"Saved: {OUTPUT_DIR}/global_tsne.png")
# -------------------------------------

X_anom_pca, IDs_anom, RADec_anom = X_pca[anomaly_mask], IDs[anomaly_mask], RADec[anomaly_mask]


# ===================================================================
# 6. Local t-SNE & DBSCAN & Plotting
# ===================================================================

if len(X_anom_pca) > 10:
    print("\nRunning Barnes-Hut t-SNE (Local Anomalies)...")
    tsne_local = openTSNE(n_components=2, perplexity=min(float(TSNE_PERPLEXITY), len(X_anom_pca)/5.0), n_jobs=-1, random_state=42)
    Y_local = np.array(tsne_local.fit(X_anom_pca))

    dbscan_local  = DBSCAN(eps=LOCAL_EPS, min_samples=LOCAL_MIN_SAMPLES, n_jobs=-1)
    labels_local  = dbscan_local.fit_predict(Y_local)
    unique_cl     = np.unique(labels_local[labels_local >= 0])
    
    print(f"Found {len(unique_cl)} anomaly micro-clusters.")

    # --- ADDED: Save Local t-SNE Plot ---
    plt.figure(figsize=(10, 8))
    scatter = plt.scatter(Y_local[:, 0], Y_local[:, 1], c=labels_local, cmap='tab20', s=30, alpha=0.8)
    plt.colorbar(scatter, label="Cluster ID (-1 = Noise)")
    plt.title(f"Local t-SNE Space of Anomalies ({len(unique_cl)} Micro-clusters)")
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    plt.savefig(f"{OUTPUT_DIR}/local_tsne.png", dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR}/local_tsne.png")
    # ------------------------------------

    # ===================================================================
    # 7. SIMBAD Cross-Match & Text File Saving
    # ===================================================================
    
    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('otype', 'main_id')
    print("\nQuerying SIMBAD for cluster centroids...")
    
    simbad_text_output = [] # <-- ADDED: List to store text
    
    for cid in unique_cl:
        mask_c   = (labels_local == cid)
        tsne_c   = Y_local[mask_c]
        centroid = tsne_c.mean(axis=0)
        rep_idx  = int(np.argmin(np.linalg.norm(tsne_c - centroid, axis=1)))
        
        rep_ra, rep_dec = RADec_anom[mask_c][rep_idx]
        
        cluster_info = f"\nCluster {cid:>3} | {mask_c.sum():>4} stars | Rep ID: {IDs_anom[mask_c][rep_idx]}"
        print(cluster_info)
        simbad_text_output.append(cluster_info)
        
        try:
            sky_coord = SkyCoord(ra=rep_ra * u.degree, dec=rep_dec * u.degree, frame='icrs')
            result    = custom_simbad.query_region(sky_coord, radius=10 * u.arcsec)
            
            if result is not None and len(result) > 0:
                cols = result.colnames
                name_col = next((c for c in ['MAIN_ID', 'main_id'] if c in cols), None)
                type_col = next((c for c in ['OTYPE', 'OTYPE_V', 'otype'] if c in cols), None)
                
                star_name = str(result[name_col][0]) if name_col else "Unknown Name"
                obj_type  = str(result[type_col][0]) if type_col else "Unknown Type"
                match_str = f"  SIMBAD -> {star_name} | Type: {obj_type}"
            else:
                match_str = "  SIMBAD -> No match found"
        except Exception as exc:
            match_str = f"  SIMBAD -> Query failed: {exc}"
            
        print(match_str)
        simbad_text_output.append(match_str)
        time.sleep(0.3) # Respect API limits
        
    # --- ADDED: Save SIMBAD Text File ---
    text_path = f"{OUTPUT_DIR}/simbad_results.txt"
    with open(text_path, "w") as f:
        f.write("\n".join(simbad_text_output))
    print(f"\nSaved: {text_path}")
    # ------------------------------------

else:
    print("\nToo few anomalies found to perform local clustering. Decrease GLOBAL_EPS.")

print("\nPipeline Complete!")