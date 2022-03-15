from schematic import CONFIG
from schematic.store.synapse import SynapseStorage
from schematic.manifest.generator import ManifestGenerator

import synapseclient

path_to_config = 'config.yml'

#projectId = 'syn22041595' # TNP-TMA
#projectId = 'syn21050481' # Vanderbilt

projectIds = {'HTAN_TNP_TMA': 'syn22041595', 
			  'HTAN_Vanderbilt': 'syn21050481',
			  'HTAN_HTAPP': 'syn20834712',
			  'HTAN_OHSU': 'syn22093319',
			  'HTAN_HMS': 'syn22123910',
			  'HTAN_BU': 'syn22124336',
			  'HTAN_CHOP': 'syn22776798',
			  'HTAN_Stanford': 'syn23511964',
			  'HTAN_MSK': 'syn23448901',
			  'HTAN_WUSTL': 'syn22255320',
			  'HTAN_DFCI': 'syn23511954',
			  'HTAN_DUKE': 'syn23511961',
			  'HTAN_TNP_Sardana': 'syn24984270',
			  'HTAN_SSRS': 'syn25555889'
			  }
breakpoint()
CONFIG.load_config(path_to_config)

syn_store = SynapseStorage()

# Load manifests into synapse
for projectId in projectIds.values():
	manifests_loaded = syn_store.upload_project_manifests_to_synapse(projectId)