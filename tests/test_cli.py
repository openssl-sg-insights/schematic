import os

import pytest

from click.testing import CliRunner

# from schematic import init
from schematic.schemas.commands import schema
from schematic.manifest.commands import manifest
from schematic.utils.google_api_utils import download_creds_file

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""

    return CliRunner()


class TestSchemaCli:
    def test_schema_convert_cli(self, runner, config_path, helpers):

        data_model_csv_path = helpers.get_data_path("example.model.csv")

        output_path = helpers.get_data_path("example.model.jsonld")

        result = runner.invoke(
            schema, ["convert", data_model_csv_path, "--output_jsonld", output_path]
        )

        assert result.exit_code == 0

        expected_substr = (
            "The Data Model was created and saved to " f"'{output_path}' location."
        )

        assert expected_substr in result.output

    # def test_get_manifest_csv(self, runner, config_path, helpers, monkeypatch):
    #     '''
    #     test manifest get command for getting a manifest in csv format

    #     '''
    #     #monkeypatch.chdir('tests/data')

    #     #output_path = os.path.abspath(os.path.join(os.getcwd(), "test.csv"))
    #     output_path = helpers.get_data_path("test.csv")


    #     print('output_path', output_path)

    #     result = runner.invoke(manifest , ["--config", config_path, "get", "--output_csv", output_path])

    #     # expected_substr = (
    #     #     f"Find the manifest template using this CSV file path: {output_path}"
    #     # )

    #     assert result.exit_code == 0
    #     # assert expected_substr in result.output

    #     # # clean up 
    #     # if os.path.exists(output_path):
    #     #     os.remove(output_path)
        

    # @pytest.mark.google_credentials_needed
    # def test_get_manifest_excel(self, runner, config_path, monkeypatch):
    #     '''
    #     test manifest get command for getting a manifest in excel format

    #     '''

    #     print("work dire", os.getcwd())
    #     monkeypatch.chdir('tests/data')

    #     # output_path = os.path.abspath(os.path.join(os.getcwd(), "test.xlsx"))

    #     # result = runner.invoke(manifest , ["--config", config_path, "get", "--output_xlsx", output_path])

    #     # expected_substr = (
    #     #     f"Find the manifest template using this Excel file path: {output_path}"
    #     # )

    #     # assert result.exit_code == 0
    #     # assert expected_substr in result.output

    #     # # clean up 
    #     # if os.path.exists(output_path):
    #     #     os.remove(output_path)