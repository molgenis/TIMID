# TIMID
TIMID model (EMX) and scripts to process new TIMID data. New data is send by someone of TIMID (at the moment Jelle Slager).

## Getting Started
This repository should make it possible to refresh the data on [timid.gcc.rug.nl](https://molgenis16.gcc.rug.nl). 
Refreshing the data contains several steps:
- Step 1: Preprocessing the raw data files (upload them to Molgenis) by using the script preprocess_raw_data.sh;
- Step 2: Combining the raw data in Molgenis with a Python script: ProcessData, which is available on timid.gcc.rug.nl.

## Step 1: Preprocessing the raw data files
- Download the preprocessing_raw_data.sh file;
- Change in this file the variables:
   - timid_dir;
   - new_dir (name of the folder in which the new files are);
   - server (check if it's the right one);
   - In case the TIMID model is on a new server / has been reuploaded, the attribute ID of mgs_species in TIMID_mgs_species_data has changed and this should be adjusted (line 106)
- Run preprocessing_raw_data.sh:
  - abcd
