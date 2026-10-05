# Part 4 Question 23/24
import json
from mcp_server.domain_server import execute_tool
import domain_agent


def test_search_by_name(query, limit=5):
    if query == "Injection":
        return {
            "ok": True,
            "data": [
                {
                    "id": 1,
                    "vulnerability_name": "SQL Injection Vulnerability"
                }
            ],
            "error": None
        }

    return {
        "ok": False,
        "data": None,
        "error": f"No vulnerabilities found matching '{query}'"
    }


def test_search_by_id(vulnerability_id):
    if vulnerability_id == 1:
        return {
            "ok": True,
            "data": {
                "id": 1,
                "vulnerability_name": "SQL Injection Vulnerability"
            },
            "error": None
        }

    return {
        "ok": False,
        "data": None,
        "error": f"No vulnerability found with ID {vulnerability_id}"
    }


def test_count_by_package(package_name):
    if package_name == "requests":
        return {
            "ok": True,
            "data": 2,
            "error": None
        }

    return {
        "ok": False,
        "data": None,
        "error": f"No package found with name '{package_name}'"
    }

test_tools = {
    "search_vulnerabilities_by_name": test_search_by_name,
    "search_vulnerabilities_by_id": test_search_by_id,
    "count_by_package": test_count_by_package
}

def run_tests():
    passed = 0
    total = 8   #edit baed on how many tests

    # Valid name search
    result = json.loads(
        execute_tool(
            "search_vulnerabilities_by_name",
            {"query": "Injection", "limit": 5},
            tools=test_tools
        )
    )

    assert result["ok"] is True
    print("PASS: search by name is valid")
    passed += 1


    # Rejected name search
    result = json.loads(
        execute_tool(
            "search_vulnerabilities_by_name",
            {"query": "ZZZZZZ", "limit": 5},
            tools=test_tools
        )
    )

    assert result["ok"] is False
    print("PASS: search by name is rejected")
    passed += 1


    # Valid ID search
    result = json.loads(
        execute_tool(
            "search_vulnerabilities_by_id",
            {"vulnerability_id": 1},
            tools=test_tools
        )
    )

    assert result["ok"] is True
    print("PASS: search by ID - valid")
    passed += 1


    # Rejected ID search
    result = json.loads(
        execute_tool(
            "search_vulnerabilities_by_id",
            {"vulnerability_id": 999999},
            tools=test_tools
        )
    )

    assert result["ok"] is False
    print("PASS: search by ID is rejected")
    passed += 1


    # Valid package count
    result = json.loads(
        execute_tool(
            "count_by_package",
            {"package_name": "requests"},
            tools=test_tools
        )
    )

    assert result["ok"] is True
    assert result["data"] == 2
    print("PASS: count by package is valid")
    passed += 1


    # Rejected package count
    result = json.loads(
        execute_tool(
            "count_by_package",
            {"package_name": "jelly"},
            tools=test_tools
        )
    )

    assert result["ok"] is False
    print("PASS: count by package is rejected")
    passed += 1

    # Part 5 safety rule - block empty search
    result = json.loads(
        execute_tool(
            "search_vulnerabilities_by_name",
            {"query": "", "limit":5},
            tools=test_tools
        )
    )
    assert result["ok"] is False
    assert result["data"] is None
    assert "safety rule" in result["error"].lower()
    print("PASS: empty vulnerability search is blocked")

    passed += 1

    # Part 5 agent loop - using MockModel, stops after reaching max_steps
    original_get_model = domain_agent.get_model
    original_execute_tool = domain_agent.execute_tool

    try:
        domain_agent.get_model = lambda: MockModel()    # Use MockModel instead of Ollama

        # Replace real db tool execution
        domain_agent.execute_tool = lambda name, inputs: json.dumps({
            "ok": True,
            "data": 2,
            "error": None
        })

        result = domain_agent.run_agent("Keep checking the package.")

        assert result["stop_reason"] == "max_steps"
        assert result["step_count"] == domain_agent.MAX_STEPS_LIMIT

        print("PASS: agent stops at max_steps")
        passed += 1

    finally:
        domain_agent.get_model = original_get_model
        domain_agent.execute_tool = original_execute_tool


    print(f"\n{passed}/{total} tests passed")

# MockModel
class MockResponse:
    def __init__(self, content):
        self.content = content


class MockModel:
    def invoke(self, messages):
        return MockResponse(json.dumps({
            "action": "tool",
            "tool": "count_by_package",
            "inputs": {
                "package_name": "requests"
            }
        }))


if __name__ == "__main__":
    run_tests()