# step3_global_tsne.py
import numpy as np
from sklearn.manifold import TSNE
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN


def main():
    X_pca = np.load("b3_pca_features.npy")
    IDs = np.load("b3_filtered_ids.npy")
    RADec = np.load("b3_filtered_radec.npy")

    n_samples = len(X_pca)
    print(f"Loaded {n_samples} stars. Running Barnes-Hut t-SNE...")

    tsne = TSNE(n_components=2, perplexity=min(30.0, n_samples / 2), method='barnes_hut', random_state=42)
    Y_global = tsne.fit_transform(X_pca)

    """
    print("Running Isolation Forest to extract top 5% anomalies...")
    iso = IsolationForest(contamination=0.05, random_state=42)
    labels = iso.fit_predict(Y_global)
    anomaly_mask = (labels == -1)
    """

    # Large epsilon to catch big normal star blobs
    dbscan_global = DBSCAN(eps=2.0, min_samples=30)
    labels_global = dbscan_global.fit_predict(Y_global)

    # In the paper: stars IN large clusters = normal, everything ELSE = anomaly candidate
    # -1 label from DBSCAN = outlier/noise = your anomalies
    anomaly_mask = (labels_global == -1)

    X_anomalies_pca = X_pca[anomaly_mask]
    IDs_anomalies = IDs[anomaly_mask]
    RADec_anomalies = RADec[anomaly_mask]

    print(f"Normal stars: {n_samples - np.sum(anomaly_mask)} | Anomalies extracted: {np.sum(anomaly_mask)}")

    plt.figure(figsize=(10, 8))
    plt.scatter(Y_global[~anomaly_mask, 0], Y_global[~anomaly_mask, 1], c='blue', label='Normal Stars', alpha=0.5, s=10)
    plt.scatter(Y_global[anomaly_mask, 0], Y_global[anomaly_mask, 1], c='red', label='Anomalies', s=15)
    plt.legend()
    plt.title("Global t-SNE: Isolation Forest Filtering")
    plt.savefig("b4_global_tsne_filter.png")

    np.save("b4_anomaly_pca.npy", X_anomalies_pca)
    np.save("b4_anomaly_radec.npy", RADec_anomalies)

    # --- THE NEW FIX: SAVE THE IDs! ---
    np.save("b4_anomaly_ids.npy", IDs_anomalies)


if __name__ == "__main__":
    main()