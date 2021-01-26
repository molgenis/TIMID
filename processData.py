"""
 20200701 Dieuwke Roelofs-Prins
 With this script:
 - The raw cult2mgs_names is processed into mgs culturable specie names
 - The mgs and cultured species data is combined 
"""

# Import module(s)
import csv
import json
import molgenis.client as molgenis
import requests
import sys
import time
from urllib.parse import parse_qs, urlparse

# Extend the molgenis client with extra functions
class molgenisExtra(molgenis.Session):
    # deze klasse bevat alle functionaliteit die ook in de normale client.Session zit
    # + de extra functionaliteit die je zelf toevoegt:

    def login_get_token(self, username, password):
        """Logs in a user and stores the acquired token in this Session object.
        Args:
        username -- username for a registered molgenis user
        password -- password for the user
        """
        response = self._session.post(self._url + "v1/login",
                                      data=json.dumps({"username": username, "password": password}),
                                      headers={"Content-Type": "application/json"})
        try:
            response.raise_for_status()
        except requests.RequestException as ex:
            self._raise_exception(ex)

        self._token = response.json()['token']
        return response.json()['token']
    
    def get_entity_metadata(self, entity):
        # This function is in the Molgenis Py client, but
        # does not use the metadata api and with that does not returns ids of the entity
        '''Retrieves the metadata for an entity repository.'''
        response = self._session.get(self._url + 'metadata/' + entity + '/attributes'
                                    , headers=
        self._get_token_header())
        response.raise_for_status()
        return response.json()    
    def update_metadata(self, entity, attribute, update):
        'Update a certain attribute of an entity'
        # Get the id of the attribute
        for item in self.get_entity_metadata(entity)['items']:
            if item['data']['name'] == attribute:
                attribute_id = item['data']['id']
        # Update the metadata
        response = self._session.patch(self._url + 'metadata/' + entity + '/attributes/' + attribute_id,
                                      headers = self._get_token_header_with_content_type(),
                                      data=json.dumps(update))
        response.raise_for_status()
        return response.status_code

    def get_idAttribute(self, entity):
        '''Retrieves all attributes with the give data_types'''
        for item in self.get_entity_metadata(entity)['items']:
                if item['data']['idAttribute']:
                    return item['data']['name']
        return None

    # New defined add_all function => possible to add more than 1000 records
    def add_all(self, entity, entities):
        '''Adds multiple entity rows to an entity repository.'''
        # Currently bulk insert is not possible with the data API => use v2 api
        row_by_row=[]
        print('Add in total', len(entities), 'entities')
        for i in range(0, len(entities), 1000):
            response = self._session.post(self._url + 'v2/' + entity,
                                         headers=self._get_token_header_with_content_type(),
                                         data=json.dumps({"entities": entities[i:i+1000]}))
            if response.status_code == 201:
                add='ok'
                #return [resource["href"].split("/")[-1] for resource in response.json()["resources"]]
            elif response.status_code == 400:
           #     if self.rest_api != 'data':
                    print(response.text)
                    errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
                    if ('for unique attribute' in errors) and ('already exists' in errors):
                        print('duplicate errors', errors)
                        row_by_row=self.add_row_by_row(entity, entities[i:i+1000])
                    else:
                        print('400 fout maar geen duplicate', errors)
                        response.raise_for_status()
            else:
                errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
                print('Error in add all function', response.status_code, errors)
                response.raise_for_status()
                return response
        return response    

    # New defined get function => using the data api
    def get_data(self, entity, page=None, batch_size=100, q=None,
            attributes=None, sortColumn=None,
            sortOrder=None,raw=False, n_records=None, expand=None):
        """Retrieves all entity rows from an entity repository.
        Args:
        entity -- fully qualified name of the entity
        q -- query in rsql format, see our RSQL documentation for details
            (https://molgenis.gitbooks.io/molgenis/content/developer_documentation/ref-RSQL.html)
        attributes -- The list of attributes to retrieve
        expand -- the attributes to expand
        num -- the maximum amount of entity rows to retrieve
        batch_size - the amount of entity rows to retrieve per time (max. 10.000)
        start -- the index of the first row to retrieve (zero indexed)
        sortColumn -- the attribute to sort on
        sortOrder -- the order to sort in
        raw -- when true, the complete REST response will be returned, rather than the data items alone
        Examples:
        >>> session = Session('http://localhost:80/api/')
        >>> session.get('Person')
        >>> session.get(entity='Person', q='name=="Henk"', attributes=['name', 'age'])
        >>> session.get(entity='Person', sort_column='age', sort_order='desc')
        >>> session.get('Person', raw=True)
        """

        if not sortColumn:  # Ensure correct ordering for batched retrieval for old Molgenis instances
            sortColumn=self.get_idAttribute(entity)

        if not attributes:
            filter=None
        else:
            filter=','.join(attributes)

        if expand:
            expand=','.join(expand)

        items = []
       
        while not n_records or len(items) < n_records:  # Keep pulling in batches
            response = self._session.get(self._url + 'data/' + entity,
                                        headers=self._get_token_header(),
                                        params={"page" : page,
                                                "size" : batch_size,
                                                "q":q,
                                                "filter": filter,
                                                "expand": expand,
                                                "sortColumn": sortColumn,
                                                "sortOrder":sortOrder})
            
            if raw:
                return response  # Simply return the first batch response JSON
            else:
                if response.status_code == 200:
                    #return response.json()["items"]
                    items.extend(response.json()["items"])
                else:
                    print(response.json())
                    errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
                    print('get error', response.status_code, errors)

            if 'next' in response.json()['links']:  # There is more to fetch
                decomposed_url = urlparse(response.json()['links']['next'])
                query_part_url = parse_qs(decomposed_url.query)
                page = query_part_url['page'][0]
            else:
                break # We caught them all


        if n_records:  # Truncate items
            items = items[:n_records] 

        print('\nTotal number of entities retrieved for entity', entity, 'is', len(items))
        return items

### Import module(s)
##import csv
##import json
##import requests
##import time
##from urllib.parse import parse_qs, urlparse
##
### Class with functions
##class Session():
##    '''Representation of a session with the MOLGENIS REST API.'''
##
##    def __init__(self, url="http://localhost:80/api/", debug=False):
##        '''Constructs a new Session.'''
##        self.url = url
##        self.debug = debug        
##        self.session = requests.Session()
##
##    def _get_token_header(self):
##        '''Creates an 'x-molgenis-token' header for the current session.'''
##        try:
##            return {"x-molgenis-token": self.token}
##        except AttributeError:
##            return {}
##
##    def _get_token_header_with_content_type(self):
##        '''Creates an 'x-molgenis-token' header for the current session and a 'Content-Type: application/json' header'''
##        headers = self._get_token_header()
##        headers.update({"Content-Type": "application/json"})
##        return headers
##        
##
##    def get_entity_meta_data(self, entity):
##        '''Retrieves the metadata for an entity repository.'''
##        response = self.session.get(self.url + 'metadata/' + entity + '/attributes'
##                                    , headers=
##        self._get_token_header())
##        response.raise_for_status()
##        return response.json()
##
##    def get_idAttribute(self, entity):
##        '''Retrieves all attributes with the give data_types'''
##        for item in self.get_entity_meta_data(entity)['items']:
##                if item['data']['idAttribute']:
##                    return item['data']['name']
##        return None
##
##    def update_metadata(self, entity, attribute, update):
##        'Update a certain attribute of an entity'
##        # Get the id of the attribute
##        for item in self.get_entity_meta_data(entity)['items']:
##            if item['data']['name'] == attribute:
##                attribute_id = item['data']['id']
##        # Update the metadata
##        response = self.session.patch(self.url + 'metadata/' + entity + '/attributes/' + attribute_id,
##                                      headers = self._get_token_header_with_content_type(),
##                                      data=json.dumps(update))
##        response.raise_for_status()
##        return response.status_code
##
##    def get(self, entity, page=None, batch_size=100, q=None,
##            attributes=None, sortColumn=None,
##            sortOrder=None,raw=False, n_records=None, expand=None):
##        """Retrieves all entity rows from an entity repository.
##        Args:
##        entity -- fully qualified name of the entity
##        q -- query in rsql format, see our RSQL documentation for details
##            (https://molgenis.gitbooks.io/molgenis/content/developer_documentation/ref-RSQL.html)
##        attributes -- The list of attributes to retrieve
##        expand -- the attributes to expand
##        num -- the maximum amount of entity rows to retrieve
##        batch_size - the amount of entity rows to retrieve per time (max. 10.000)
##        start -- the index of the first row to retrieve (zero indexed)
##        sortColumn -- the attribute to sort on
##        sortOrder -- the order to sort in
##        raw -- when true, the complete REST response will be returned, rather than the data items alone
##        Examples:
##        >>> session = Session('http://localhost:80/api/')
##        >>> session.get('Person')
##        >>> session.get(entity='Person', q='name=="Henk"', attributes=['name', 'age'])
##        >>> session.get(entity='Person', sort_column='age', sort_order='desc')
##        >>> session.get('Person', raw=True)
##        """
##
##        if not sortColumn:  # Ensure correct ordering for batched retrieval for old Molgenis instances
##            sortColumn=self.get_idAttribute(entity)
##
##        if not attributes:
##            filter=None
##        else:
##            filter=','.join(attributes)
##
##        if expand:
##            expand=','.join(expand)
##
##        items = []
##       
##        while not n_records or len(items) < n_records:  # Keep pulling in batches
##            response = self.session.get(self.url + 'data/' + entity,
##                                        headers=self._get_token_header(),
##                                        params={"page" : page,
##                                                "size" : batch_size,
##                                                "q":q,
##                                                "filter": filter,
##                                                "expand": expand,
##                                                "sortColumn": sortColumn,
##                                                "sortOrder":sortOrder})
##            
##            if raw:
##                return response  # Simply return the first batch response JSON
##            else:
##                if response.status_code == 200:
##                    #return response.json()["items"]
##                    items.extend(response.json()["items"])
##                else:
##                    print(response.json())
##                    errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
##                    print('get error', response.status_code, errors)
##
##            if 'next' in response.json()['links']:  # There is more to fetch
##                decomposed_url = urlparse(response.json()['links']['next'])
##                query_part_url = parse_qs(decomposed_url.query)
##                page = query_part_url['page'][0]
##            else:
##                break # We caught them all
##
##
##        if n_records:  # Truncate items
##            items = items[:n_records] 
##
##        print('\nTotal number of entities retrieved for entity', entity, 'is', len(items))
##        return items
##
##
##    def add_all(self, entity, entities):
##        '''Adds multiple entity rows to an entity repository.'''
##        # Can only post 1000 a time
##        # Currently bulk insert is not possible with the data API => use v2 api
##        row_by_row=[]
##        print('Add in total', len(entities), 'entities')
##        print(entities[0])
##        for i in range(0, len(entities), 1000):
##            response = self.session.post(self.url + 'v2/' + entity,
##                                         headers=self._get_token_header_with_content_type(),
##                                         data=json.dumps({"entities": entities[i:i+1000]}))
##            if response.status_code == 201:
##                add='ok'
##                #return [resource["href"].split("/")[-1] for resource in response.json()["resources"]]
##            elif response.status_code == 400:
##           #     if self.rest_api != 'data':
##                    print(response.text)
##                    errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
##                    if ('for unique attribute' in errors) and ('already exists' in errors):
##                        row_by_row=self.add_row_by_row(entity, entities[i:i+1000])
##                    else:
##                        print('400 fout maar geen duplicate', errors)
##                        response.raise_for_status()
##            else:
##                errors = json.loads(response.content.decode("utf-8"))['errors'][0]['message']
##                print('Error in add all function', response.status_code, errors)
##                response.raise_for_status()
##                return response
##        return response
##
##    def delete_data(self, entity, q=None):
##        '''Deletes all data from an entity and any entities that are referenced by'''
##        entity_emptied = False
##        while not entity_emptied:
##            response = self.session.delete(self.url + "data/" + entity, headers=self._get_token_header_with_content_type())
##            if response.status_code != 204:
##                errors = json.loads(response.content.decode("utf-8"))['detail']
##                if ('referenced by entity') in errors:
##                    ref_entity=errors.split("referenced by entity",1)[1].replace('.', '').replace("'", '').strip()
##                    print('Delete the data from the referenced entity', ref_entity)
##                    response = self.session.delete(self.url + "data/" + ref_entity, headers=self._get_token_header_with_content_type())
##                else:
##                    raise SystemExit(errors)
##            else:
##                entity_emptied = True
##        return response    

# Define variable(s)
species_list=[]
combined={}
cult_added={}
cult_freq={}
cultured2mgs={}
file_id={}
mgs_add={}
mgs2cultured={}
mgs_cult_data=[]
mgs_plot_files=[]
mgs_plots_right_role=[]
read_plot_roles=['TIMID_VIEWER']
sample_info=[]
#token='0301e8400b6c42509b3062ac4eaddb19'

if len(sys.argv) == 1:
    raise SystemExit('Start script with server and password parameters!')

timid_url=sys.argv[1]+'/api/'
timid_pwd=sys.argv[2]
timid_session = molgenisExtra(timid_url)
token=timid_session.login_get_token('admin', timid_pwd)

######## Get the raw cult2mgs data ######
cult2mgs_data=timid_session.get_data('TIMID_cult2mgs_names', batch_size=1000)

if len(cult2mgs_data) == 0:
    raise SystemExit('No raw data found?!?')

## Get the mgs bug specie names from the mgs specie data as it appears
## that not all mgs species are in the cult2mgs_names dataset

######## Get the mgs specie data ######
mgs_data=timid_session.get_data('TIMID_mgs_species_data', batch_size=1000) #, q='TIMID_ID==''TIMID_21185''')

if len(mgs_data) == 0:
    raise SystemExit('No mgs data found?!?')

######## Get the sample info data ######
# For simplification change all xref datatypes to string to get the actual xref-value
update={'type': 'string'}
timid_session.update_metadata('TIMID_sample_info', 'Research_center', update)
timid_session.update_metadata('TIMID_sample_info', 'Cohort', update)
#timid_session.update_metadata('TIMID_sample_info', 'Phenotype', update)
time.sleep(60)
TIMID_sample_info=timid_session.get('TIMID_sample_info', batch_size=1000) #, q='TIMID_ID==''TIMID_21185''')

if len(TIMID_sample_info) == 0:
    raise SystemExit('No Sample Info data found in TIMID ?!?')

# Change the datatypes back again
update={'type': 'categorical', 'refEntityType':'TIMID_research_centra'}
timid_session.update_metadata('TIMID_sample_info', 'Research_center', update)
update={'type': 'categorical', 'refEntityType':'TIMID_cohorts'}
timid_session.update_metadata('TIMID_sample_info', 'Cohort', update)
#update={'type': 'xref', 'refEntityType':'TIMID_phenotypes'}
#timid_session.update_metadata('TIMID_sample_info', 'Phenotype', update)

# Save the sample_info in a list of dictionaries
i=1
for content_row in TIMID_sample_info:
    phenotype=[]
    for pheno in content_row['Phenotype']:
        phenotype.append(pheno['id'])
    if i==1:
        print('Sample Info Cohort:', content_row['Cohort'])
        print('Sample Info Research Center:', content_row['Research_center'])
        print('Sample Info Phenotype:', phenotype)

    sample_info.append({'TIMID_ID': content_row['TIMID_ID'],
                        'Cohort': content_row['Cohort'],
                        'Research_center': content_row['Research_center'],
                        'Phenotype': phenotype})

    if i==1:
        print(sample_info[-1]['Cohort'])
    i=0

######## Get the ids and the names of the MGS plots (files) ######
mgs_plots=timid_session.get_data('sys_FileMeta', batch_size=1000, q='filename=like=''TIMID''', attributes=['id', 'filename'])
if len(mgs_plots) == 0:
    raise SystemExit('No mgs plots found?!?')

for file_info in mgs_plots:
    file_id[file_info['data']['filename'][0:11]]=file_info['data']['id']

######## Get the cultured specie data ######
# For getting the actual xref-value change datatype of organism to string
update={'type': 'string'}
timid_session.update_metadata('TIMID_cultured_species', 'Organism', update)
time.sleep(30)
cultured_data=timid_session.get_data('TIMID_cultured_species', batch_size=1000)

if len(cultured_data) == 0:
    raise SystemExit('No cultured specie data found?!?')

# Change the datatype back again
update={'type': 'xref', 'refEntityType':'TIMID_culturable_species'}
timid_session.update_metadata('TIMID_cultured_species', 'Organism', update)

i=1
for content_row in cultured_data:
    check=[i for i, d in enumerate(sample_info) if content_row['data']['TIMID_ID'] in d.values()]
    if len(check) == 0:
        print('No sample information yet for TIMID', content_row['data']['TIMID_ID'])
        try:
            sample_info.append({'TIMID_ID': content_row['data']['TIMID_ID'],
                            'Cohort': 'Unknown',
                            'Research_center': 'Unknown',
                            'Phenotype': ['unknown'],
                            'mgs_performed': 'N',
                            'culturomics_performed': 'Y',
                            'mgs_plots': file_id[content_row['data']['TIMID_ID']]})
        except:
            sample_info.append({'TIMID_ID': content_row['data']['TIMID_ID'],
                            'Cohort': 'Unknown',
                            'Research_center': 'Unknown',
                            'Phenotype': ['unknown'],
                            'mgs_performed': 'N',
                            'culturomics_performed': 'Y'})
                   
    else:
        try:
            sample_info[check[0]]['culturomics_performed'] = 'Y'
            sample_info[check[0]]['mgs_performed'] = 'N'
            sample_info[check[0]]['mgs_plots'] = file_id[content_row['data']['TIMID_ID']]
        except:
            sample_info[check[0]]['culturomics_performed'] = 'Y'
            sample_info[check[0]]['mgs_performed'] = 'N'
                        
    if i == 1:
        print(content_row['data']['TIMID_ID'])
        print(content_row['data']['Organism'])
    i=0
        

    cult_freq.setdefault(content_row['data']['TIMID_ID'], {})
    # Cultured bug species can occur more than once as they can be cultured
    # under different circumstances/media
    if content_row['data']['Organism'] in cult_freq[content_row['data']['TIMID_ID']].keys():
        cult_freq[content_row['data']['TIMID_ID']][content_row['data']['Organism']] = cult_freq[content_row['data']['TIMID_ID']][content_row['data']['Organism']] + content_row['data']['Cultured_frequency']
        print(content_row['data']['TIMID_ID'], 'has multiple records for bug', content_row['data']['Organism'])
    else:
        cult_freq[content_row['data']['TIMID_ID']][content_row['data']['Organism']] = content_row['data']['Cultured_frequency']
    
# Process the raw cult2mgs names data
for content_row in cult2mgs_data:
    metagenomics=content_row['data']['Metagenomics']
    cultured_species=content_row['data']['Cultured']
#   Unknown mgs_species (.) are renamed to Unknown
    mgs_species_name=metagenomics.replace(".",'Unknown')
#   Store the mgs species name with corresponding cultured species name(s)
    mgs2cultured.setdefault(mgs_species_name,[])
    mgs2cultured[mgs_species_name].append(cultured_species)
#   Store the cultured bug specie name with the corresponding mgs species name    
    cultured2mgs.setdefault(cultured_species)
    cultured2mgs[cultured_species]=mgs_species_name

# Add any missing species names which are in the mgs species data but not in cult2mgs_names
for content_row in mgs_data:
    if not content_row['data']['mgs_species'] in mgs2cultured.keys():
        mgs2cultured.setdefault(content_row['data']['mgs_species'], ['Unknown'])

# Process data into the Mapping of cultured to metagenomics species names entity
# Store the data in a list with dictionaries in stead of a dictionary with lists
for mgs_species, culturable_species in mgs2cultured.items():
    species_list.append({'mgs_species': mgs_species, 'culturable_species':culturable_species})

# So far so good
# Delete content of the table (if the shell script to preprocess the data ran
# correct there is no data left).
delete=timid_session.delete('TIMID_mgs_culturable_species')

timid_session.add_all('TIMID_mgs_culturable_species', species_list)

# Now these data is added, the type of attribute mgs_species in TIMID_mgs_species_data
# can be re-adjusted to xref again
update={'type': 'xref', 'refEntityType':'TIMID_mgs_culturable_species'}
timid_session.update_metadata('TIMID_mgs_species_data', 'mgs_species', update)

# The last step is to combine the mgs and cultured species information
for mgs in mgs_data:    
    del mgs['data']['ID']
    if mgs['data']['mgs_abundance'] < 0.0001 : mgs['data']['abundance_level'] = '1'
    if mgs['data']['mgs_abundance'] >= 0.0001 and mgs['data']['mgs_abundance'] < 0.001 : mgs['data']['abundance_level'] = '2'
    if mgs['data']['mgs_abundance'] >= 0.001 and mgs['data']['mgs_abundance'] < 0.01 : mgs['data']['abundance_level'] = '3'
    if mgs['data']['mgs_abundance'] >= 0.01 and mgs['data']['mgs_abundance'] <= 0.1 : mgs['data']['abundance_level'] = '4'
    if mgs['data']['mgs_abundance'] > 0.1 : mgs['data']['abundance_level'] = '5'

#   Check if sample info is known of the sample in mgs_specie_data
#   If not add this sample
#   If yes add the info to the mgs cultured combined dataset
    sample_info_key=[i for i, d in enumerate(sample_info) if mgs['data']['TIMID_ID'] in d.values()]
    if len(sample_info_key) == 0:
        try:
            sample_info.append({'TIMID_ID': mgs['data']['TIMID_ID'],
#                                'Cohort': [], 'Research_center': [], 'Phenotype': [], 
                            'mgs_performed': 'Y', 'culturomics_performed': 'N',
                            'mgs_plots': file_id[mgs['data']['TIMID_ID']]})
        except:
            sample_info.append({'TIMID_ID': mgs['data']['TIMID_ID'],
                            'mgs_performed': 'Y', 'culturomics_performed': 'N'})            
    else:
        if 'culturomics_performed' in sample_info[sample_info_key[0]].keys() and sample_info[sample_info_key[0]]['culturomics_performed'] == 'Y':
            sample_info[sample_info_key[0]]['mgs_performed']='Y'
            mgs['data']['research_center']=sample_info[sample_info_key[0]]['Research_center']
            mgs['data']['cohort']=sample_info[sample_info_key[0]]['Cohort']
            mgs['data']['phenotype']=','.join(sample_info[sample_info_key[0]]['Phenotype'])
            #mgs['data']['phenotype']=sample_info[sample_info_key[0]]['Phenotype']

        else:
            try:
                sample_info[sample_info_key[0]]['mgs_performed']='Y'
                sample_info[sample_info_key[0]]['culturomics_performed']='N'
                sample_info[sample_info_key[0]]['mgs_plots'] = file_id[mgs['data']['TIMID_ID']]
                mgs['data']['research_center']=sample_info[sample_info_key[0]]['Research_center']
                mgs['data']['cohort']=sample_info[sample_info_key[0]]['Cohort']
                mgs['data']['phenotype']=','.join(sample_info[sample_info_key[0]]['Phenotype'])
                #mgs['data']['phenotype']=sample_info[sample_info_key[0]]['Phenotype']
            except:
                sample_info[sample_info_key[0]]['mgs_performed']='Y'
                sample_info[sample_info_key[0]]['culturomics_performed']='N'                
                mgs['data']['research_center']=sample_info[sample_info_key[0]]['Research_center']
                mgs['data']['cohort']=sample_info[sample_info_key[0]]['Cohort']
                mgs['data']['phenotype']=','.join(sample_info[sample_info_key[0]]['Phenotype'])

    mgs['data']['culturable_species']=mgs2cultured[mgs['data']['mgs_species']]
    if mgs['data']['TIMID_ID'] in cult_freq.keys():
        i=0
        for cultured_species in mgs2cultured[mgs['data']['mgs_species']]:
            if cultured_species in cult_freq[mgs['data']['TIMID_ID']].keys():
                i=i+1
                if 'n_cultures' in mgs['data'].keys():
                    mgs['data']['n_cultures']=mgs['data']['n_cultures']+cult_freq[mgs['data']['TIMID_ID']][cultured_species]
                else: mgs['data']['n_cultures']=cult_freq[mgs['data']['TIMID_ID']][cultured_species]

                # Store which TIMID_ID cultured_species is combined 
                combined.setdefault(mgs['data']['TIMID_ID'], {})
                combined[mgs['data']['TIMID_ID']][cultured_species] = 'Y'
                
        if i>1:
            print('Multiple cultured records for mgs bug',mgs['data']['mgs_species'], 'and ID', mgs['data']['TIMID_ID'])
            
    if 'Unknown' in mgs['data']['culturable_species']:
        mgs['data']['culturable'] = 'N'
    else: mgs['data']['culturable'] = 'Y'
#    if 'n_cultures' in mgs['data'].keys():
#        if mgs['data']['n_cultures']==0: mgs['data']['culturable']='N'
#        if mgs['data']['n_cultures']>0: mgs['data']['culturable']='Y'
#    else: mgs['data']['culturable']='-'


    mgs_cult_data.append(mgs['data'])

species=0
ids=0
for key in combined.keys():
    # print(key, len(combined[key]))
    for key2 in combined[key].keys():
        species=species+1
    ids=ids+1
print('Number of TIMID ids with mgs and cultured information', ids, 'number of species', species)

# Add the cultured species data of IDs/species that are not in the mgs data
for cult_data in cultured_data:
    if combined.get(cult_data['data']['TIMID_ID'], {}).get(cult_data['data']['Organism']) == None:
        # Store the relevant information and set some default values
        if cult_added.get(cult_data['data']['TIMID_ID'], {}).get(cult_data['data']['Organism']) == None:
            mgs_add['TIMID_ID']=cult_data['data']['TIMID_ID']
            mgs_add['mgs_species']=cultured2mgs[cult_data['data']['Organism']]
            mgs_add['culturable_species']=cult_data['data']['Organism']
            mgs_add['abundance_level']='0'
            mgs_add['n_cultures']=cult_freq[cult_data['data']['TIMID_ID']][cult_data['data']['Organism']]
            mgs_add['culturable']='Y'
            sample_info_key=[i for i, d in enumerate(sample_info) if cult_data['data']['TIMID_ID'] in d.values()]
            if len(sample_info_key) > 0:
                mgs_add['research_center']=sample_info[sample_info_key[0]]['Research_center']
                mgs_add['cohort'] = sample_info[sample_info_key[0]]['Cohort']
                mgs_add['phenotype'] = ','.join(sample_info[sample_info_key[0]]['Phenotype'])
                #mgs_add['phenotype'] = sample_info[sample_info_key[0]]['Phenotype']
            mgs_cult_data.append(mgs_add)
            mgs_add={}
            cult_added.setdefault(cult_data['data']['TIMID_ID'], {})
            cult_added[cult_data['data']['TIMID_ID']][cult_data['data']['Organism']]='Y'
    elif combined.get(cult_data['data']['TIMID_ID'], {}).get(cult_data['data']['Organism']) == 'Y':
        None
        # print('TIMID ID', cult_data['data']['TIMID_ID'], 'with bug specie', cult_data['data']['Organism'], 'already exists')
    else:
        print('That\'s strange', cult_data['data']['TIMID_ID'], cult_data['data']['Organism'], combined[cult_data['data']['TIMID_ID']][cult_data['data']['Organism']])


# Delete content of the table (if the shell script to preprocess the data ran
# correct there is no data left).
delete=timid_session.delete('TIMID_sample_info')
# timid_session.add_all('TIMID_sample_info', sample_info)
# Write sample info to file as it seems not to be possible to upload the data
# including the sys_FileMeta ID for mgs_plots

sample_info_file=open('/Users/dieuwke.roelofs-prins/Documents/Projects/TIMID/TIMID_sample_info.csv', 'w')

header=[]

for column_name in sample_info[0].keys():
    header.append(column_name)

sample_info_csv = csv.DictWriter(sample_info_file, fieldnames=header, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
sample_info_csv.writeheader()    

for row in sample_info:
    #row['Cohort']=','.join(row['Cohort'])
    #row['Research_center']=','.join(row['Research_center'])
    row['Phenotype']=','.join(row['Phenotype'])
    if 'culturomics_performed' not in row.keys():
        row['culturomics_performed'] = 'N'
    if 'mgs_performed' not in row.keys():
            row['mgs_performed'] = 'N'

    # Store the linked mgs_plots
    if 'mgs_plots' in row.keys():
        mgs_plot_files.append(row['mgs_plots'])

    sample_info_csv.writerow(row)

sample_info_file.close()

input('Press Enter when uploading sample_info has finished')
print('\n''')

# Delete content of the table (if the shell script to preprocess the data ran
# correct there is no data left).
delete=timid_session.delete('TIMID_mgs_cultured_data')

# Upload the combined MGS and cultured information into TIMID_mgs_cultured_data
timid_session.add_all('TIMID_mgs_cultured_data', mgs_cult_data)

# Finally set view permissions for the mgs_plot files to the TIMID_viewer role
    
# Get the Metadata information of the files. 
FileMeta = requests.get(timid_url + 'permissions/entity-sys_FileMeta', headers = {"x-molgenis-token": token}).json()

for file in FileMeta['data']['objects']:
    current_role_permissions = []
    # Check the file type
    if file['id'] in mgs_plot_files:
        # A file can have multiple permissions for different users/roles
        for permissions in file['permissions']:
            if 'role' in permissions:
                current_role_permissions.append(permissions['role'])
        # Check if the roles that should have read permissions have them, otherwise add the read permission to the file    
        for role in read_plot_roles:
            if role not in current_role_permissions:
                print('update permission role', role, 'for file', file['label'])
                response = requests.post(timid_url + 'permissions/entity-sys_FileMeta/' + file['id'],
                              headers = {'Content-Type': 'application/json', "x-molgenis-token": token},
                              data=json.dumps({'permissions': [{'permission': 'READ',
                                                        'role': role }]}))
                if response.status_code != 201:
                    print('Something went wrong while updating permissions', response)
                mgs_plots_right_role.append(file['id'])
            else: mgs_plots_right_role.append(file['id'])

if len(mgs_plots_right_role) != len(mgs_plot_files):
    print('Not all mgs plot files have read permissions for', read_plot_roles)
    print('Number of mgs_plot_files in sample info is', len(mgs_plot_files))
    print('Number of files with the right permissions is', len(mgs_plots_right_role))
else:
    print('Number of files having the right permissions is', len(mgs_plots_right_role))

print('FINISHED')

