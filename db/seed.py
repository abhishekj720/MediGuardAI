"""Seed the Insforge Postgres database with disease reference data.

Usage:
    python db/seed.py

This creates the `diseases` table and populates it with common conditions
that link ICD-10 codes to CPT procedure codes, providing a shared reference
for both the doctor and insurance agents.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.db import execute_sql

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    icd10_code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    common_procedures TEXT[] NOT NULL,
    severity_level VARCHAR(20) NOT NULL CHECK (severity_level IN ('mild', 'moderate', 'severe'))
);
"""

SEED_DATA = [
    ("E11.9", "Type 2 Diabetes Mellitus", "A chronic condition affecting how the body processes blood sugar (glucose). Requires ongoing monitoring and management.", "{99213,99214,36415}", "moderate"),
    ("I10", "Essential Hypertension", "Persistently elevated blood pressure in the arteries. A major risk factor for heart disease and stroke.", "{99213,93000,36415}", "moderate"),
    ("M17.11", "Primary Osteoarthritis, Right Knee", "Degenerative joint disease of the right knee causing pain, stiffness, and reduced mobility.", "{99213,27447,29881}", "moderate"),
    ("J06.9", "Acute Upper Respiratory Infection", "Common cold or viral infection of the upper respiratory tract. Usually self-limiting.", "{99213,71046}", "mild"),
    ("F32.1", "Major Depressive Disorder, Moderate", "A mood disorder causing persistent feelings of sadness and loss of interest that interferes with daily life.", "{99214,90837}", "moderate"),
    ("G43.909", "Migraine, Unspecified", "Recurring headaches of moderate to severe intensity, often with nausea and sensitivity to light.", "{99214,70553}", "moderate"),
    ("K21.0", "Gastroesophageal Reflux Disease (GERD)", "Chronic digestive disease where stomach acid flows back into the esophagus, causing heartburn.", "{99213,43239}", "mild"),
    ("M54.5", "Low Back Pain", "Pain in the lower back region, one of the most common reasons for medical visits.", "{99213,99214,71046}", "mild"),
    ("J45.20", "Mild Intermittent Asthma", "A chronic lung condition that causes airways to narrow and swell, producing extra mucus.", "{99213,71046,93000}", "mild"),
    ("I25.10", "Coronary Artery Disease", "Build-up of plaque in the heart's arteries, reducing blood flow and increasing heart attack risk.", "{99214,93000,36415,71046}", "severe"),
]

INSERT_SQL = """
INSERT INTO diseases (icd10_code, name, description, common_procedures, severity_level)
VALUES ($1, $2, $3, $4::TEXT[], $5)
ON CONFLICT (icd10_code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    common_procedures = EXCLUDED.common_procedures,
    severity_level = EXCLUDED.severity_level;
"""


async def seed():
    print("Creating diseases table...")
    await execute_sql(CREATE_TABLE_SQL)

    print("Seeding disease data...")
    for row in SEED_DATA:
        await execute_sql(INSERT_SQL, list(row))
        print(f"  Seeded: {row[1]} ({row[0]})")

    print(f"\nDone! Seeded {len(SEED_DATA)} diseases.")


if __name__ == "__main__":
    asyncio.run(seed())
