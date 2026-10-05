import json
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP
from web_application.backend.models import Vulnerability, Package
from web_application.backend.database import SessionLocal

mcp = FastMCP("vulnerabilities")

import time
from sqlalchemy import text

QUERY_TIMEOUT_MS = 5000  # MS

# Attemps to show retry behavior for Q19
TEST_RETRY_ATTEMPTS = 0

# MCP STDIO logs must go to stderr
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_with_retries(func, retries=3, delay=0.1, fail_attempt=0):
    for attempt in range(retries):
        try:
            logger.info(f"Attempt {attempt + 1} of {retries}")

            if attempt < fail_attempt:
                raise RuntimeError("Simulated failure for testing retries.")
            result = func()
            logger.info(f"Attempt {attempt + 1} succeeded.")
            return result
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                raise

@mcp.tool()
def search_vulnerabilities_by_name(query: str, limit: int=5):
    """
    Input:
        query (str): The search query for vulnerability names.
        limit (int): The maximum number of results to return.
    """
    db = SessionLocal()
    try:
        db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT_MS}"))

        try:
            vulnerabilities = run_with_retries(lambda: db.query(Vulnerability)
                .filter(Vulnerability.vulnerability_name.ilike(f"%{query}%"))
                .limit(limit)
                .all(),
                fail_attempt=TEST_RETRY_ATTEMPTS)
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Error occurred while searching vulnerabilities: {str(e)}"
            }
        if not vulnerabilities:
            return {
                "ok": False,
                "data": None,
                "error": f"No vulnerabilities found matching '{query}'"
            }

        results = []
        for vulnerability in vulnerabilities:
            results.append({
                "id": vulnerability.id,
                "vulnerability_name": vulnerability.vulnerability_name,
                "vulnerability_code": vulnerability.vulnerability_code,
                "urgency_score": vulnerability.urgency_score,
                "package_id": vulnerability.package_id
            })

        return {"ok" : True,
                "data" : results,
                "error" : None}
    finally:
        db.close()

@mcp.tool()
def search_vulnerabilities_by_id(vulnerability_id: int):
    """
    Input:
        vulnerability_id (int): The ID of the vulnerability to search for.
    """
    db = SessionLocal()
    try:
        db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT_MS}"))
        try:
            vulnerability = run_with_retries(lambda: db.query(Vulnerability)
                .filter(Vulnerability.id == vulnerability_id)
                .first(),
                fail_attempt=TEST_RETRY_ATTEMPTS)
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Error occurred while searching vulnerability: {str(e)}"
            }

        if not vulnerability:
            return {"ok" : False,
                    "data" : None,
                    "error" : f"No vulnerability found with ID {vulnerability_id}"}
        
        return {"ok" : True,
                "data": {
                "id": vulnerability.id,
                "vulnerability_name": vulnerability.vulnerability_name,
                "vulnerability_code": vulnerability.vulnerability_code,
                "urgency_score": vulnerability.urgency_score,
                "package_id": vulnerability.package_id
            },
                "error" : None}
    finally:
        db.close()

@mcp.tool()
def count_by_package(package_name: str):
    """
    Count the number of vulnerabilities associated with a specific package.

    Input:
        package_name (str): The name of the package to search for.
    """
    db = SessionLocal()
    try:
        db.execute(text(f"SET SESSION MAX_EXECUTION_TIME = {QUERY_TIMEOUT_MS}"))
        try:
            package = run_with_retries(lambda: db.query(Package)
            .filter(Package.name == package_name)
            .first(),
            fail_attempt=TEST_RETRY_ATTEMPTS)
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Error occurred while searching for package: {str(e)}"
            }
        if not package:
            return {
                "ok": False,
                "data": None,
                "error": f"No package found with name '{package_name}'"
            }

        try:
            count = run_with_retries(lambda: db.query(Vulnerability)
            .filter(Vulnerability.package_id == package.id)
            .count(),
            fail_attempt=TEST_RETRY_ATTEMPTS)
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Error occurred while counting vulnerabilities: {str(e)}"
            }

        return {"ok": True, "data": count, "error": None}
    finally:
        db.close()

# Part 4 Question 22
def execute_tool(name, inputs, tools=None): #temporary fixturs so tests can run offline
    try:
        if tools is None:
            tools = {
                "search_vulnerabilities_by_name" : search_vulnerabilities_by_name,
                "search_vulnerabilities_by_id" : search_vulnerabilities_by_id,
                "count_by_package" : count_by_package
            }
        # Part 5 safety rule
        if name == "search_vulnerabilities_by_name":
            query = inputs.get("query")
            if not query or not query.strip():
                return json.dumps({
                    "ok" : False,
                    "data": None,
                    "error": "There is a safety rule: vulnerability search cannot be empty"
                })

        if name not in tools:
            result = {
                "ok" : False,
                "data" : None,
                "error": f"Tool '{name}' not found."
            }
        elif name == "search_vulnerabilities_by_name":
            result = tools[name](query=inputs.get("query"), limit=inputs.get("limit", 5))
        elif name == "search_vulnerabilities_by_id":
            result = tools[name](vulnerability_id=inputs.get("vulnerability_id"))
        elif name == "count_by_package":
            result = tools[name](package_name=inputs.get("package_name"))

        return json.dumps(result)
    
    except Exception as e:
        return json.dumps({
            "ok": False,
            "data": None,
            "error": f"Error occurred while executing tool: {str(e)}"
        }
        )

if __name__ == "__main__":
    mcp.run()
