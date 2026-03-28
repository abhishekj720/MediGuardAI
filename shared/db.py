import os
import httpx
from dotenv import load_dotenv

load_dotenv()

INSFORGE_API_KEY = os.getenv("INSFORGE_API_KEY", "")
INSFORGE_API_BASE_URL = os.getenv("INSFORGE_API_BASE_URL", "http://localhost:7130")


def get_insforge_headers() -> dict:
    return {
        "Authorization": f"Bearer {INSFORGE_API_KEY}",
        "Content-Type": "application/json",
    }


async def execute_sql(query: str, params: list | None = None) -> dict:
    """Execute a SQL query against the Insforge Postgres database."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{INSFORGE_API_BASE_URL}/api/db/query",
            headers=get_insforge_headers(),
            json={"query": query, "params": params or []},
        )
        response.raise_for_status()
        return response.json()


async def get_diseases() -> list[dict]:
    """Fetch all diseases from the database."""
    result = await execute_sql("SELECT * FROM diseases ORDER BY name")
    return result.get("rows", [])


async def execute_rpc(function_name: str, params: dict) -> list[dict]:
    """Call a Postgres function (RPC) via Insforge and return the rows."""
    # Build a parameterized SELECT call to the function
    param_placeholders = ", ".join(f"${i+1}" for i in range(len(params)))
    query = f"SELECT * FROM {function_name}({param_placeholders})"
    result = await execute_sql(query, list(params.values()))
    return result.get("rows", [])


async def get_disease_by_icd10(icd10_code: str) -> dict | None:
    """Fetch a disease by ICD-10 code."""
    result = await execute_sql(
        "SELECT * FROM diseases WHERE icd10_code = $1", [icd10_code]
    )
    rows = result.get("rows", [])
    return rows[0] if rows else None
