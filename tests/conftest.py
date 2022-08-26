from multiprocessing.sharedctypes import Value
import os
import logging
import platform

import shutil
import pytest
import pandas as pd
from dotenv import load_dotenv, find_dotenv

from schematic.schemas.explorer import SchemaExplorer
from schematic.configuration import CONFIG
from schematic.utils.df_utils import load_df

load_dotenv()


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# Silence some very verbose loggers
logging.getLogger("urllib3").setLevel(logging.INFO)
logging.getLogger("googleapiclient").setLevel(logging.INFO)
logging.getLogger("google_auth_httplib2").setLevel(logging.INFO)


TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(TESTS_DIR, "data")
CONFIG_PATH = os.path.join(DATA_DIR, "test_config.yml")
CONFIG.load_config(CONFIG_PATH)
GREAT_EXPECTATION_DIR = os.path.join(TESTS_DIR, "great_expectations")

@pytest.fixture
def dataset_id():
    yield "syn25614635"


# This class serves as a container for helper functions that can be
# passed to individual tests using the `helpers` fixture. This approach
# was required because fixture functions cannot take arguments.
class Helpers:
    @staticmethod
    def get_great_expectation_dir(path, *paths):
        return os.path.join(GREAT_EXPECTATION_DIR, path, *paths)


    @staticmethod
    def get_data_file(path, *paths, **kwargs):
        fullpath = os.path.join(DATA_DIR, path, *paths)
        return open(fullpath, **kwargs)

    @staticmethod
    def get_data_frame(path, *paths, **kwargs):
        fullpath = os.path.join(DATA_DIR, path, *paths)
        return load_df(fullpath, **kwargs)

    @staticmethod
    def get_schema_explorer(path=None, *paths):
        if path is None:
            return SchemaExplorer()

        fullpath = Helpers.get_data_path(path, *paths)

        se = SchemaExplorer()
        se.load_schema(fullpath)
        return se

    @staticmethod
    def get_version_specific_manifest_path(self, path):
        version=platform.python_version()
        manifest_path = self.get_data_path(path)
        temp_manifest_path = manifest_path.replace('.csv',version[0:3]+'.csv')
        return temp_manifest_path

    @staticmethod
    def get_version_specific_syn_dataset():
        version=platform.python_version()

        synId = None

        if version.startswith('3.7'):
            synId = 'syn34999062'
        elif version.startswith('3.8'):
            synId = 'syn34999080'
        elif version.startswith('3.9'):
            synId = 'syn34999096'

        if not synId:
            raise OSError(
                "Unsupported Version of Python"
            )
        else:
            return synId

@pytest.fixture
def helpers():
    yield Helpers


@pytest.fixture
def config():
    yield CONFIG


@pytest.fixture
def config_path():
    yield CONFIG_PATH
