# step4_anomaly_simbad.py
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.simbad import Simbad
import warnings

# Suppress the messy NoResultsWarning from Astroquery to keep the terminal clean
from astroquery.exceptions import NoResultsWarning

warnings.filterwarnings('ignore', category=NoResultsWarning)


def main():
    X_anomalies_pca = np.load("b4_anomaly_pca.npy")
    ra_dec_anomalies = np.load("b4_anomaly_radec.npy")

    # Load the IDs saved from Step 3
    try:
        ids_anomalies = np.load("b4_anomaly_ids.npy")
    except FileNotFoundError:
        print("Error: Could not find 'b4_anomaly_ids.npy'. Please run the updated Step 3 first!")
        return

    if len(X_anomalies_pca) < 2:
        print("Not enough anomalies to run t-SNE.")
        return

    print(f"Running Local t-SNE on {len(X_anomalies_pca)} anomalies...")
    tsne_local = TSNE(n_components=2, perplexity=min(15.0, len(X_anomalies_pca) - 1), method='barnes_hut',
                      random_state=42)
    Y_local = tsne_local.fit_transform(X_anomalies_pca)

    print("Clustering anomalies using DBSCAN...")
    dbscan = DBSCAN(eps=1.5, min_samples=3)
    labels = dbscan.fit_predict(Y_local)

    unique_clusters = np.unique(labels[labels >= 0])
    print(f"Found {len(unique_clusters)} distinct anomaly micro-clusters.")

    custom_simbad = Simbad()
    custom_simbad.add_votable_fields('otype', 'main_id')

    for cluster_id in unique_clusters:
        mask = (labels == cluster_id)
        cluster_coords = ra_dec_anomalies[mask]
        cluster_ids = ids_anomalies[mask]
        cluster_tsne_points = Y_local[mask]
        centroid = cluster_tsne_points.mean(axis=0)
        distances = np.linalg.norm(cluster_tsne_points - centroid, axis=1)
        representative_idx = np.argmin(distances)
        galah_id = cluster_ids[representative_idx]
        ra, dec = cluster_coords[representative_idx]

        print(f"\n--- Querying Cluster {cluster_id} ({np.sum(mask)} stars) ---")
        """
        # Grab the GALAH ID and coordinates of the first star in the cluster
        galah_id = cluster_ids[0]
        ra, dec = cluster_coords[0][0], cluster_coords[0][1]
        """
        c = SkyCoord(ra=ra * u.degree, dec=dec * u.degree, frame='icrs')

        print(f"Representative GALAH ID: {galah_id}")

        try:
            result = custom_simbad.query_region(c, radius=10 * u.arcsec)

            # CRITICAL FIX: Check if result exists AND has actual rows
            if result is not None and len(result) > 0:
                colnames = result.colnames

                if 'MAIN_ID' in colnames:
                    star_name = result['MAIN_ID'][0]
                elif 'main_id' in colnames:
                    star_name = result['main_id'][0]
                else:
                    star_name = "Unknown Name"

                if isinstance(star_name, bytes):
                    star_name = star_name.decode('utf-8')

                if 'OTYPE' in colnames:
                    obj_type = result['OTYPE'][0]
                elif 'OTYPE_V' in colnames:
                    obj_type = result['OTYPE_V'][0]
                elif 'otype' in colnames:
                    obj_type = result['otype'][0]
                else:
                    obj_type = "Unclassified Type"

                if isinstance(obj_type, bytes):
                    obj_type = obj_type.decode('utf-8')

                print(f"Simbad Match: {star_name} | Type: {obj_type}")
            else:
                print("Simbad Match: No match found (Uncatalogued Star)")
        except Exception as e:
            print(f"Query failed due to network/API error: {e}")

    # ==========================================
    # ADDED PLOTTING CODE HERE
    # ==========================================
    print("\nGenerating and saving t-SNE plot for anomalies...")
    plt.figure(figsize=(10, 8))

    # Scatter plot, color-coded by DBSCAN labels (-1 is noise, >=0 are distinct clusters)
    scatter = plt.scatter(Y_local[:, 0], Y_local[:, 1], c=labels, cmap='tab20', s=30, alpha=0.8)

    # Add a colorbar to identify the clusters
    plt.colorbar(scatter, label="Cluster ID (-1 = Noise)")

    plt.title(f"Local t-SNE Space of Anomalies ({len(unique_clusters)} Micro-clusters)")
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")

    plt.savefig("b5_anomaly_tsne.png")
    plt.close()
    print("Plot successfully saved as 'b5_anomaly_tsne.png'.")


if __name__ == "__main__":
    main()