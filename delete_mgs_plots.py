"""
 202101 Dieuwke Roelofs-Prins
 With this script:
 - The .png MGS plot files can be deleted from sys_FileMeta
"""

# Import module(s)
import molgenis.client as molgenis
import sys

# Define variables
ids_list = []
timid_url=sys.argv[1]+'/api/'
timid_pwd=sys.argv[2]
timid_session = molgenis.Session(timid_url)
timid_session.login('admin', timid_pwd)


######## Get the ids and the names of the MGS plots (files) ######
mgs_plots=timid_session.get('sys_FileMeta', batch_size=1000, q='filename=like=''TIMID''', attributes='id,filename,contentType')
if len(mgs_plots) == 0:
    raise SystemExit('No mgs plots found?!?')
else: print('Number of current MGS plots is', len(mgs_plots))

for file_info in mgs_plots:
    if file_info['contentType'] != 'image/png':
        print(file_info['filename'], 'is no MGS plot file and won''t be removed')
    else:
        ids_list.append(file_info['id'])

print('Number of MGS plots to be deleted is', len(ids_list))

for i in range(0, len(ids_list), 1000):
    delete=timid_session.delete_list('sys_FileMeta', ids_list[i:i+1000])
    if delete.status_code == 204:
        print('MGS plot files successfully deleted')
    else:
        print('MGS plot files not successfully deleted', delete)

print('FINISHED')
