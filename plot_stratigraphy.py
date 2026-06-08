import json
import glob
import numpy as np
import matplotlib.pyplot as plt

# Extract data
depths = []
cu_vals = []
k_vals = []

files = sorted(glob.glob('Site_1/json_report/Sample_1-*.json'))
for f in files:
    with open(f) as file:
        data = json.load(file)
        c = data.get('Coefficients', {})
        # Extract depth from name, e.g., 'Sample_1-10' -> 10
        name = data['Sample_Name']
        depth = int(name.split('-')[1])
        
        depths.append(depth)
        cu_vals.append(c.get('Cu', np.nan))
        k_vals.append(c.get('K_hazen_cms', np.nan))

# Sort by depth for proper plotting
sort_idx = np.argsort(depths)
depths = np.array(depths)[sort_idx]
cu_vals = np.array(cu_vals)[sort_idx]
k_vals = np.array(k_vals)[sort_idx]

plt.rcParams.update({'font.size': 12})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 8), sharey=True)

# Plot Cu
ax1.plot(cu_vals, depths, marker='o', linestyle='-', color='b', markersize=8, linewidth=2)
ax1.set_xlabel('Uniformity Coefficient ($C_u$)', fontweight='bold')
ax1.set_ylabel('Height Above Pit Base (m)', fontweight='bold')
ax1.set_title('Vertical Profile of $C_u$', fontweight='bold')
ax1.grid(True, linestyle='--', alpha=0.7)
# Usually depth is top-down, but here 0 is base, 10 is surface.
# So 10 is top, 0 is bottom. Let's not invert y-axis. Normal y-axis: 0 at bottom, 10 at top.

# Plot K
ax2.plot(k_vals, depths, marker='D', linestyle='-', color='r', markersize=8, linewidth=2)
ax2.set_xscale('log')
ax2.set_xlabel('Hydraulic Conductivity ($K_{Hazen}$)[cm/s]', fontweight='bold')
ax2.set_title('Vertical Profile of Permeability', fontweight='bold')
ax2.grid(True, which="both", linestyle='--', alpha=0.7)

# Highlight anomaly
ax1.axhline(y=9, color='green', linestyle='--', alpha=0.5)
ax1.text(cu_vals[np.where(depths==9)[0][0]]+5, 9.2, 'Permeable Layer', color='green', fontweight='bold')

ax2.axhline(y=9, color='green', linestyle='--', alpha=0.5)
ax2.text(k_vals[np.where(depths==9)[0][0]]/3, 9.2, 'Permeable Layer', color='green', fontweight='bold')

plt.suptitle('Site 1: Stratigraphic Geotechnical Assessment', fontsize=16, fontweight='bold', y=0.95)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])
plt.savefig('Site_1_Stratigraphy.png', dpi=300)
print("Saved Site_1_Stratigraphy.png")
