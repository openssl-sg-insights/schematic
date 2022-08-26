import os
import logging
import shutil
import pytest
import yaml
from schematic.models.metadata import MetadataModel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@pytest.fixture
def metadata_model(helpers):

    metadata_model = MetadataModel(
        inputMModelLocation=helpers.get_data_path("example.model.jsonld"),
        inputMModelLocationType="local",
    )

    yield metadata_model

@pytest.fixture 
def get_input_token(config_path):

    if os.getenv('INPUT_TOKEN'):
        token = os.getenv('INPUT_TOKEN')
    else: 
        synapse_config_dict = yaml.load(config_path)
        print(synapse_config_dict)
        SYNAPSE_CONFIG_PATH = synapse_config_dict['definitions']['synapse_config']
        config_dict = yaml.load(SYNAPSE_CONFIG_PATH)
        token = config_dict['authtoken']
    yield token


@pytest.fixture
def manifest_submission_output(metadata_model, helpers, get_input_token):
    manifest_record_type = 'table'
    restrict_rules = False
    manifestPath = helpers.get_data_path("mock_manifests/Example_mock_component.csv")

    output = metadata_model.submit_metadata_manifest(path_to_json_ld = helpers.get_data_path("example.model.jsonld"), manifest_path=manifestPath, dataset_id='syn27221721', validate_component='MockComponent', input_token=get_input_token, 
        manifest_record_type = manifest_record_type, restrict_rules = restrict_rules)

    # Clean-up
    if os.path.isdir(helpers.get_great_expectation_dir(f"uncommitted")):
        shutil.rmtree(helpers.get_great_expectation_dir(f"uncommitted"))

    yield output 

class TestManifestSubmission:
    def test_manifest_submission(self, manifest_submission_output):
        assert isinstance(manifest_submission_output, str)
        assert len(manifest_submission_output) > 0