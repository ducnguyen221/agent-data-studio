"""Power BI Service queries keep bearer tokens on the intended endpoint."""

import pytest

from powerbi_agent import tools_query


DATASET_ID = "cfafbeb1-8037-4d0c-896e-a46fb27ff229"
QUERY = 'EVALUATE ROW("Count", 1)'


class ToolRegistry:
    def tool(self):
        def register(function):
            setattr(self, function.__name__, function)
            return function

        return register


def service_tool(monkeypatch):
    registry = ToolRegistry()
    tools_query.register(registry)
    monkeypatch.setattr(tools_query.policy, "check_dax", lambda *_args, **_kwargs: (True, ""))
    monkeypatch.setattr(tools_query.policy, "audit", lambda *_args, **_kwargs: None)
    return registry.execute_dax_service


@pytest.mark.parametrize("bad_id", ["", "../groups/elsewhere", "https://example.invalid", DATASET_ID + "/../x", DATASET_ID + "\n"])
def test_invalid_dataset_id_never_reads_token_or_sends_request(monkeypatch, bad_id):
    tool = service_tool(monkeypatch)

    def unexpected(*_args, **_kwargs):
        raise AssertionError("An invalid dataset ID reached a credential or network boundary")

    monkeypatch.setattr(tools_query, "get_azure_token", unexpected)
    monkeypatch.setattr(tools_query.requests, "post", unexpected)
    assert "Mã dataset không hợp lệ" in tool(bad_id, QUERY)


@pytest.mark.parametrize("payload", [
    {"error": {"message": "SYNTHETIC_PRIVATE_CANARY"}},
    {"error": {}},
    {"results": [{"error": {"message": "SYNTHETIC_PRIVATE_CANARY"}}]},
    {"results": [{"error": {}}]},
    {"results": [{"tables": [{"error": {"message": "SYNTHETIC_PRIVATE_CANARY"}}]}]},
    {"results": [{"tables": [{"error": {}}]}]},
])
def test_http_200_service_errors_are_not_reported_as_empty_data(monkeypatch, payload):
    tool = service_tool(monkeypatch)
    monkeypatch.setattr(tools_query, "get_azure_token", lambda: "SYNTHETIC_TOKEN")
    seen = []

    class Response:
        status_code = 200

        def json(self):
            return payload

    def post(url, **kwargs):
        seen.append((url, kwargs))
        return Response()

    monkeypatch.setattr(tools_query.requests, "post", post)
    message = tool(DATASET_ID, QUERY)
    assert "trả lỗi truy vấn" in message
    assert "SYNTHETIC_PRIVATE_CANARY" not in message
    assert seen[0][0] == f"https://api.powerbi.com/v1.0/myorg/datasets/{DATASET_ID}/executeQueries"
    assert seen[0][1]["headers"]["Authorization"] == "Bearer SYNTHETIC_TOKEN"
