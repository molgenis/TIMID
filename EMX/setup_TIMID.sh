# Choose the right server to upload the EMX to
echo 'Choose the right server'
mcmd config set host

# Add the EMX
echo 'Set up the TIMID model'
mcmd import --with-action add -p TIMID_EMX.xlsx

# Add reference data
echo 'Add reference data'
mcmd import --with-action add -p TIMID_abundance_levels.tsv --in TIMID
mcmd import --with-action add -p TIMID_cohorts.tsv --in TIMID
mcmd import --with-action add -p TIMID_media.tsv --in TIMID
mcmd import --with-action add -p TIMID_methods.tsv --in TIMID
mcmd import --with-action add -p TIMID_oxygen_requirements.tsv --in TIMID
mcmd import --with-action add -p TIMID_phenotypes.tsv --in TIMID
mcmd import --with-action add -p TIMID_refs.tsv --in TIMID
mcmd import --with-action add -p TIMID_research_centra.tsv --in TIMID
