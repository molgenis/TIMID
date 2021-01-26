# TIMID
TIMID model (EMX) and scripts to process new TIMID data. New data is send by someone of TIMID (at the moment Jelle Slager).

## Getting Started
This repository should make it possible to refresh the data on [timid.gcc.rug.nl](https://timid.gcc.rug.nl). 
Refreshing the data contains several steps:
- Step 1: Preprocessing the raw data files (upload them to Molgenis) by using the script preprocess_raw_data.sh;
- Step 2: Combining the raw data in Molgenis with the Python script: ProcessData.py. This script also needs to be run locally as a file is created which should be uploaded manually. 

## Step 1: Preprocessing the raw data files
- Download the preprocessing_raw_data.sh file;
- Change in this file the variables:
   - server (check if it's the right one);
   - timid_dir;
   - new_dir (name of the folder in which the new files are);
   - In case the TIMID model is on a new server / has been reuploaded, the attribute ID of mgs_species in TIMID_mgs_species_data has changed and this should be adjusted (line 110). The right ID can be found on the server in entity=sys_md_Attribute, look for attribute mgs_species.
- Run preprocessing_raw_data.sh:
  1.) First the new files are adjusted (renaming and adding of headers);
  2.) Secondly the raw and processed data that is in Molgenis is deleted. This includes the MGS plots (files). These files are deleted with the Python script: delete_mgs_plots.py, make sure this is in the same folder as the preprocessing_raw_data.sh;
  3.) In the third step the new (raw) data is uploaded, including the new MGS plots (files);
  
## Step2: Combining the raw data files
