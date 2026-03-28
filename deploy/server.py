import sys
from pathlib import Path

# Add project root to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from insurance.agent import get_insurance_quote, list_available_procedures
from orchestrator.agent import run_orchestrator
from shared.schemas import DemoRequest, DemoResponse

app = FastAPI(
    title="MediGuardAI",
    description="Multi-agent medical workflow orchestration demo",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://em6x2e4c.insforge.site",
        "https://*.insforge.site",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "MediGuardAI"}


@app.get("/api/procedures")
async def get_procedures():
    """List all available procedure codes for the UI dropdown."""
    return list_available_procedures()


@app.post("/api/demo", response_model=DemoResponse)
async def run_demo(request: DemoRequest):
    """Run the full orchestration demo: doctor notes -> insurance check -> patient explanation."""
    try:
        result = await run_orchestrator(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insurance/{procedure_code}")
async def get_quote(procedure_code: str, patient_id: str = "default"):
    """Direct insurance quote lookup (for Dev 2 testing)."""
    quote = get_insurance_quote(procedure_code, patient_id)
    return quote
