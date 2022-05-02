import schemathesis
from hypothesis import settings
from schematic.configuration import CONFIG
import os
import pytest
import configparser

schema = schemathesis.from_path(
    "api/openapi/openapi.json", base_url="http://127.0.0.1:3001/v1"
)


@schema.parametrize(endpoint="/manifest/generate")
@settings(deadline=None)
def test_manifest_generator(case):
    case.call_and_validate(timeout=30)


@pytest.fixture
def auth_token():
    """Fixture for loading authentication"""
    # reading configuation data from .SynapseConfig
    config = configparser.ConfigParser()
    synapse_config = config.read(".synapseConfig")
    token = config['authentication']['authtoken']

    return token

@schema.parametrize(endpoint="/manifest/download")
@settings(deadline=None)
def test_manifest_download(case, auth_token):
    print(case.body)
    #case.body['input_token'] = auth_token
    #case.call_and_validate(timeout=30)