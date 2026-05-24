# step2_normalize_pca.py
import numpy as np
from sklearn.decomposition import PCA


def main():
    print("Loading pre-normalized uniform spectra, IDs, and coordinates...")
    X = np.load("b2_uniform_spectra.npy")
    IDs = np.load("b2_processed_ids.npy")
    RADec = np.load("b2_processed_radec.npy")

    print(f"Original batch size: {X.shape[0]} stars")

    # 1. Clean out bad data (e.g., completely flat/zeroed spectra)
    # A standard normalized spectrum should have a mean near 1.0.
    # If it's 0, it's a dead file.
    means = np.mean(X, axis=1)
    good_mask = (means > 0.1) & ~np.isnan(X).any(axis=1)

    X_clean = X[good_mask]
    IDs_clean = IDs[good_mask]
    RADec_clean = RADec[good_mask]

    print(f"Dropped {len(X) - len(X_clean)} dead/invalid spectra.")
    print(f"Valid stars remaining: {len(X_clean)}")

    if len(X_clean) == 0:
        print("Error: No valid spectra left to process! Cannot continue.")
        return

    # 2. PCA Pre-filtering
    # The GALAH paper used top 50 components. If we have fewer than 50 stars, use that instead.
    n_components = min(50, X_clean.shape[0])

    # Continuum normalization: divide each spectrum by its median
    medians = np.median(X_clean, axis=1, keepdims=True)
    medians[medians == 0] = 1.0  # guard against division by zero
    X_normalized = X_clean / medians

    print(f"Running PCA to reduce {X_normalized.shape[1]} dimensions down to {n_components}...")
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_normalized)

    variance_kept = np.sum(pca.explained_variance_ratio_) * 100
    print(f"Kept {variance_kept:.2f}% of the physical variance.")

    # Save outputs for Step 3
    np.save("b3_pca_features.npy", X_pca)
    np.save("b3_filtered_ids.npy", IDs_clean)
    np.save("b3_filtered_radec.npy", RADec_clean)
    print("SUCCESS! Ready for Step 3.")


if __name__ == "__main__":
    main()