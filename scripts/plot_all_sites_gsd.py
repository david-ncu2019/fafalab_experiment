"""
Script to plot a master composite GSD curve overlaying all samples across all site folders.
Output: outputs/All_Sites_GSD_Summary.png
"""

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.sieve_analysis.input import calculate_sieve_distribution
from scripts.sieve_analysis.visualization import plot_all_sites_composite_gsd

SITE_FOLDERS = ["Site_1", "Site_1_9", "Site_4", "Site_5", "Site_8"]


def main():
    sites_data: dict[str, list[dict]] = {}

    for folder_name in SITE_FOLDERS:
        folder_path = REPO_ROOT / folder_name
        if not folder_path.exists():
            continue

        clean_site = (
            folder_name.replace("Site_", "")
            .replace("1_9", "1*9")
            .replace("1-9", "1*9")
        )
        site_key = f"Site {clean_site}"

        csv_files = sorted(folder_path.glob("*.csv"))
        samples = []
        for csv_file in csv_files:
            try:
                raw_df = pd.read_csv(csv_file)
                df, _ = calculate_sieve_distribution(raw_df, csv_file)
                samples.append({"sample_name": csv_file.stem, "df": df})
            except Exception as err:
                print(f"Skipping {csv_file.name}: {err}")

        if samples:
            sites_data[site_key] = samples

    if not sites_data:
        print("No site data found!")
        return 1

    fig = plot_all_sites_composite_gsd(sites_data)

    outputs_dir = REPO_ROOT / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    output_path = outputs_dir / "All_Sites_GSD_Summary.png"
    fig.savefig(output_path, dpi=600, bbox_inches="tight")
    plt.close(fig)

    print(f"Successfully generated master composite plot -> {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
