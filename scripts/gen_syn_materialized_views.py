'''
Purpose:
	Want to start scoping how to create materialized views within Synapse
	between a manifest table and a fileview.

'''

from synapseclient.table import MaterializedViewSchema
import synapseclient


# Perform join from filevew to manifest.

#manifest_synid = 'syn27726926' #Biospecimen TNP TMA
#fileview_id = 'syn27648522' # Imaging Level 2 Fileview TNP TMA

projectId = 'syn21050481' # Vanderbilt
manifest_synid = 'syn27736629' #biospecimen manifest vanderbilt
fileview_id = 'syn27728255' #sc_rnaseq_level1 fileview vanderbilt

syn_config_path = '/Users/mialydefelice/Documents/schematic_b/schematic/.synapseConfig'
syn = synapseclient.Synapse(configPath=syn_config_path)
# this will save to only the staging version of the repo...
# this would actually be really helpful for testing!
#syn.setEndpoints(**synapseclient.client.STAGING_ENDPOINTS)
syn.login(silent=True)

temp = MaterializedViewSchema(
    name="biospecimen_M_scRNAseqL1_FV_mat_view",
    parent=projectId,
    definingSQL=f"SELECT * FROM {manifest_synid} M JOIN {fileview_id} F ON (M.HTANBiospecimenID = F.HTANParentBiospecimenID)"
)

ent = syn.store(temp)
breakpoint()

