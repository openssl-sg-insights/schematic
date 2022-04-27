import schemathesis
from hypothesis import settings

schema = schemathesis.from_path(
    "api/openapi/openapi.json", base_url="http://127.0.0.1:3001/v1"
)

@schema.parametrize(endpoint="/manifest/generate")
@settings(deadline=None)
def test_manifest_generator(case):
    case.call_and_validate(timeout=30)