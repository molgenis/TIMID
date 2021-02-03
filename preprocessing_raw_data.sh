# December 2020 Dieuwke Roelofs-Prins
# Script to:
# - preprocess the TIMID data
# - delete the old data from Molgenis
# - import the new data into Molgenis

# Functions
check_process()
 {
  if [ $1 == 0 ]; then
    echo "Step $2 went OK"
    else echo "Step $2 did not go OK, further processing has stopped"
         exit
  fi
}

# Variables
server=https://molgenis16.gcc.rug.nl
#server=http://localhost

timid_dir=/Users/XXXX/Documents/Projects/TIMID
input_dir=$timid_dir/input
new_dir=mgs_and_cmx_201127
mgs_dir=$timid_dir/$new_dir
mgs_data=$mgs_dir/mgs_tables
mgs_plots=$mgs_dir/mgs_plots

echo $mgs_data

# STEP 1 Adjust files (add headers and rename)
# STEP 1a Check if input_dir exists and remove all input files
#         otherwise create input_dir

if [ ! -d "$input_dir" ]; then
  # Create input_dir if $input_dir does not exist. 
  echo "Creating folder ${input_dir}"
  mkdir $input_dir
elif [ "$(ls -A $input_dir)" ]; then
   rm  $input_dir/*
   check_process $? 1a
else
    echo "$input_dir is empty"
fi

# STEP 1b and c Add header to and rename culturable_species file 
echo "culturable_species\nUnknown" >$input_dir/TIMID_culturable_species.tsv
check_process $? 1b
cat $mgs_dir/culturable_species.tsv >>$input_dir/TIMID_culturable_species.tsv
check_process $? 1c
# Step 1d Rename file cult2mgs_names
cp $mgs_dir/cult2mgs_names.tsv $input_dir/TIMID_cult2mgs_names.tsv 
check_process $? 1d
# Step 1e Rename file cultured_species
cp $mgs_dir/cultured_species.tsv $input_dir/TIMID_cultured_species.tsv 
check_process $? 1e
# Step 1f Rename file sample_info.tsv
cp $mgs_dir/sample_info.tsv $input_dir/TIMID_sample_info.tsv 
check_process $? 1f
# Step 1g and 1h Combine all the sample mgs specie data
echo "TIMID_ID\tmgs_species\tmgs_abundance" > $input_dir/TIMID_mgs_species_data.tsv
check_process $? 1g
for file in $mgs_data/*.txt
   do
     filename="${file##*/}"
     awk -v filename=$filename '{print substr(filename, 1, 11), $0}' OFS='\t' $file >> $input_dir/TIMID_mgs_species_data.tsv
   done
check_process $? 1h

# STEP 2 Delete the current raw and processed data in Molgenis
# Prompt for the password of the used server
read -s -p "Password of $server to upload data into: " password
# First define the right host in mcmd.yaml
mcmd config set host
check_process $? 2a
# Delete the data from the TIMID server
mcmd delete --data TIMID_mgs_cultured_data -f
check_process $? 2b
mcmd delete --data TIMID_sample_info -f
check_process $? 2c
mcmd delete --data TIMID_mgs_species_data -f
check_process $? 2d
mcmd delete --data TIMID_cultured_species -f
check_process $? 2e
mcmd delete --data TIMID_mgs_culturable_species -f
check_process $? 2f
mcmd delete --data TIMID_sample_info -f
check_process $? 2g
mcmd delete --data TIMID_cult2mgs_names -f
check_process $? 2h
mcmd delete --data TIMID_culturable_species -f
check_process $? 2i
echo 'Delete the current MGS plots'
python3 delete_mgs_plots.py $server $password
check_process $? 2j

echo ""
echo "Upload the available data"
# Step 3 Upload the available data
cd input
mcmd import -p -a add TIMID_culturable_species.tsv
check_process $? 3a
mcmd import -p -a add TIMID_cult2mgs_names.tsv
check_process $? 3b
mcmd import -p -a add TIMID_cultured_species.tsv
check_process $? 3c
mcmd import -p -a add TIMID_sample_info.tsv
check_process $? 3d
# Before importing the mgs_specie_data first adjust the model as there
# is not yet data available in TIMID_mgs_culturable_species
# echo With password for admin is meant password for Molgenis16
curl -u "admin:"$password"" -X PATCH $server/api/metadata/TIMID_mgs_species_data/attributes/aaaac5x7v3qad6qwh3hsujiabe -H "Content-Type: application/json" -H "accept: */*" -d "{"type":"string"}"
check_process $? 3e
mcmd import -p -a add TIMID_mgs_species_data.tsv
check_process $? 3f

## Step 3g Upload the mgs plots
echo 'Upload the MGS plots, this may take a while'
for file in $mgs_plots/TIMID*.png
   do
    filename="${file##*/}"
    curl -u "admin:"$password"" -X POST $server/api/files -H 'Content-Type: image/png'  -H 'x-molgenis-filename: '"$filename"'' --data-binary @$file
   done
check_process $? 3g
 

echo "The first step of processing the TIMID data has finished"
echo "Wait a few minutes on indexing to be finished and then run the script ProcessData"
echo "Be aware that the file TIMID_sample_info.csv is created an has to be uploaded manually"
