# TIMID
TIMID model (EMX) and scripts to process new TIMID data. New data is send by someone of TIMID (at the moment Jelle Slager).

## Getting Started
This repository should make it possible to refresh the data on the [TIMID](https://timid.molgeniscloud.org){:target="_blank" rel="noopener"} server. 
Refreshing the data contains several steps:
- Step 1: Preprocessing the raw data files (upload them to Molgenis) by using the script preprocess_raw_data.sh;
- Step 2: Combining the raw data in Molgenis with the Python script: ProcessData.py. This script also needs to run locally as a file with sample information is created which has to be uploaded manually. This is because there is a link to sys_FileMeta in it and the add function within the Molgenis Py-client can not handle this properly (yet). 

## Step 1: Preprocessing the raw data files
- Download the preprocessing_raw_data.sh file;
- Change in this file the variables:
   - server (check if it's the right one);
   - timid_dir;
   - new_dir (name of the folder in which the new files are);
   - In case the TIMID model is on a new server / has been reuploaded, the attribute ID of mgs_species in TIMID_mgs_species_data has changed and this should be adjusted (line 110 in the script). The right ID can be found on the [server](https://timid.molgeniscloud.org/menu/main/dataexplorer?entity=sys_md_Attribute&hideselect=true&mod=data&filter=entity==TIMID_mgs_species_data;name=q=mgs_species), look for attribute mgs_species.
- Run preprocessing_raw_data.sh:
  - First the new files are adjusted (renaming and adding of headers);
  - Secondly the raw and processed data that is in Molgenis is deleted. This includes the MGS plots (files). These files are deleted with the Python script: delete_mgs_plots.py, make sure this is in the same folder as the preprocessing_raw_data.sh script;
  - In the third step the new (raw) data is uploaded, including the new MGS plots (files);
  
## Step 2: Combining the raw data files
By running the script processData.py the raw Metagenomics and cultured data are combined. This script combines the information from TIMID_mgs_species_data and TIMID_cultured_species and links the MGS plots to the samples in TIMID_sample_info.
Please following the logging on the screen / or check you log file (if created) because when the script has nearly finished you have to upload the file with the TIMID_sample_info manually: First check if the right host is selected, then upload the data (run in the same folder as where the file is):
```
mcmd config set host
mcmd import -p -a add TIMID_sample_info.csv
```

## Step 3: Perform some checks
When everything ran successfully checks that can be done are:
- Check the output of the logging (or log-file);
- Check some file-counts vs data in the corresponding entities;

