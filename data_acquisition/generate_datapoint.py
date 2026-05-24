# Generate Datapoints

import os
from astropy.table import Table

# --- Configuration ---
fits_file = "galah_dr4_allspec_240705.fits"
master_file = "galah_ids.txt"

# Hardcoded variables
n = 500  # Number of datapoints per new file
m = 100  # Number of new files to generate

# --- Step 1: Read existing IDs to avoid duplicates ---
print(f"Checking {master_file} for existing IDs...")
existing_ids = set()

if os.path.exists(master_file):
    with open(master_file, "r") as f:
        content = f.read().strip()
        if content:
            # Split by comma and load into a set for fast O(1) lookups
            existing_ids = set(content.split(","))

print(f"Found {len(existing_ids)} existing IDs.")

# --- Step 2: Read FITS file and extract new IDs ---
print("Reading FITS file...")
tbl = Table.read(fits_file)

print("Filtering for new data points...")
new_ids = []
target_count = n * m

# Iterate through the table and grab IDs we haven't seen yet
for x in tbl["sobject_id"]:
    sid = str(x)
    if sid not in existing_ids:
        new_ids.append(sid)
        # Stop once we hit the requested n * m amount
        if len(new_ids) == target_count:
            break

actual_count = len(new_ids)
print(f"Collected {actual_count} new spectra to process.")

# --- Step 3: Distribute to m files and append to master list ---
if actual_count == 0:
    print("No new data points available in the FITS file.")
else:
    # 1. Write the new datapoints into m separate CSV files
    files_created = 0
    for i in range(m):
        # Slice the list into chunks of size n
        chunk = new_ids[i * n: (i + 1) * n]

        if not chunk:
            break  # Break early if we run out of new IDs before filling m files

        output_file = f"new_ids_batch_{i + 1}.csv"
        with open(output_file, "w") as f:
            f.write(",".join(chunk))
        files_created += 1

    print(f"Saved new IDs across {files_created} CSV file(s).")

    # 2. Append the new datapoints to the master galah_ids.txt file
    with open(master_file, "a") as f:
        # If the master file already has content, add a leading comma before appending
        if len(existing_ids) > 0:
            f.write(",")
        f.write(",".join(new_ids))

    print(f"Successfully appended {actual_count} new IDs to {master_file}.")