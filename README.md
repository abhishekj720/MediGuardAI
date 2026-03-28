# MediGuardAI

Multi-agent medical workflow orchestration demo. This application demonstrates how AI agents can collaborate to process doctor notes, check insurance coverage, and generate patient-friendly explanations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (React + Vite + TypeScript)                │
│                     http://localhost:5173                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Orchestrator API                         │
│                   (FastAPI + Uvicorn)                        │
│                     http://localhost:8000                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ Orchestrator│  │  Insurance  │  │   Patient   │          │
│  │    Agent    │──│    Agent    │──│    Agent    │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌──────────────────────┐        ┌──────────────────────┐
│    Anthropic API     │        │   Insforge Database  │
│   (Claude AI Model)  │        │     (PostgreSQL)     │
└──────────────────────┘        └──────────────────────┘
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Anthropic API Key** - Get one at [console.anthropic.com](https://console.anthropic.com)
- **Insforge API Key** - For database access

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd MediGuardAI

# Copy environment variables
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
INSFORGE_API_KEY=your_insforge_api_key_here
INSFORGE_API_BASE_URL=http://localhost:7130
```

### 3. Install Backend Dependencies

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all Python dependencies
pip install -r orchestrator/requirements.txt
pip install -r patient/requirements.txt
pip install -r insurance/requirements.txt
```

### 4. Seed the Database

```bash
python db/seed.py
```

This creates the `diseases` table with ICD-10 codes, procedure codes, and medical reference data.

### 5. Start the Backend Server

```bash
# From project root, with venv activated
uvicorn orchestrator.server:app --reload --port 8000
```

The API will be available at: http://localhost:8000

### 6. Install and Start Frontend

```bash
# In a new terminal
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:5173

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/procedures` | List available procedure codes |
| POST | `/api/demo` | Run full orchestration workflow |
| GET | `/api/insurance/{procedure_code}` | Direct insurance quote lookup |

## Project Structure

```
MediGuardAI/
├── orchestrator/           # Main orchestration agent
│   ├── agent.py            # Multi-agent orchestration logic
│   ├── server.py           # FastAPI server
│   └── tools.py            # Tool definitions for agents
├── patient/                # Patient explanation agent
│   ├── agent.py            # Patient-friendly explanations
│   └── models.py           # Data models
├── insurance/              # Insurance quote agent
│   ├── agent.py            # Insurance processing logic
│   └── models.py           # Data models
├── shared/                 # Shared utilities
│   ├── db.py               # Database access layer
│   └── schemas.py          # Pydantic schemas
├── db/
│   └── seed.py             # Database seeding script
├── frontend/               # React frontend
│   ├── src/
│   └── package.json
└── .qoder/
    └── agents/             # Custom AI agents for development
```

## Development

### Running Tests

```bash
# Backend tests (if available)
pytest

# Frontend tests
cd frontend && npm test
```

### Code Formatting

```bash
# Python
ruff check . --fix
ruff format .

# Frontend
cd frontend && npm run lint
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'shared'"**
- Run the server from the project root directory
- Ensure venv is activated

**"ANTHROPIC_API_KEY not set"**
- Verify `.env` file exists and contains your API key
- Restart the server after modifying `.env`

**"Connection refused to Insforge"**
- Check `INSFORGE_API_BASE_URL` in `.env`
- Ensure Insforge service is running

**Frontend can't connect to backend**
- Verify backend is running on port 8000
- Check CORS settings in `orchestrator/server.py`

## License

See [LICENSE](LICENSE) for details.
