"""Generate realistic test fixture PDFs simulating legacy insurance policy documents.

Usage:
    pip install reportlab
    python insurance/fixtures/generate_pdfs.py

Produces 5 PDFs in insurance/fixtures/pdfs/ that contain the same 10 CPT codes
from mock_insurance.json, distributed across documents the way real insurance
data is fragmented.
"""

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).parent.parent.parent
MOCK_DATA_PATH = PROJECT_ROOT / "insurance" / "data" / "mock_insurance.json"
OUTPUT_DIR = Path(__file__).parent / "pdfs"


def load_mock_data() -> dict:
    with open(MOCK_DATA_PATH) as f:
        return json.load(f)


def get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=20,
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=16,
        spaceAfter=8,
        textColor=colors.HexColor("#1a3c6e"),
    ))
    styles.add(ParagraphStyle(
        name="SubHead",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.grey,
    ))
    return styles


# ──────────────────────────────────────────────────────────────────────
# PDF 1: Policy Coverage Schedule
# ──────────────────────────────────────────────────────────────────────

def generate_policy_coverage_schedule(data: dict, output_dir: Path, styles):
    doc = SimpleDocTemplate(
        str(output_dir / "policy_coverage_schedule.pdf"),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    story.append(Paragraph("MediGuard Health Plan — Policy Coverage Schedule", styles["DocTitle"]))
    story.append(Paragraph("Plan Year 2024 | Group Policy #MG-2024-PPO-500 | Effective 01/01/2024", styles["BodyText2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This schedule details the covered procedures under your MediGuard Preferred Provider "
        "Organization (PPO) plan. Coverage percentages reflect in-network benefits after the "
        "annual deductible of $500 per individual / $1,500 per family has been met. "
        "Out-of-network services are covered at 50% of the allowed amount.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Schedule of Covered Procedures", styles["SectionHead"]))

    table_data = [["CPT Code", "Procedure Name", "Coverage %", "Copay", "Coinsurance", "Network Tier", "Prior Auth"]]

    # Derived data to make PDFs richer than mock JSON
    extra = {
        "99213": {"copay": "$25", "coinsurance": "20%", "tier": "Primary Care"},
        "99214": {"copay": "$40", "coinsurance": "20%", "tier": "Primary Care"},
        "27447": {"copay": "$250", "coinsurance": "30%", "tier": "Surgical"},
        "70553": {"copay": "$75", "coinsurance": "15%", "tier": "Diagnostic Imaging"},
        "43239": {"copay": "$50", "coinsurance": "10%", "tier": "Diagnostic Procedure"},
        "93000": {"copay": "$0", "coinsurance": "0%", "tier": "Diagnostic"},
        "90837": {"copay": "$25", "coinsurance": "25%", "tier": "Behavioral Health"},
        "29881": {"copay": "$150", "coinsurance": "20%", "tier": "Surgical"},
        "36415": {"copay": "$0", "coinsurance": "0%", "tier": "Lab Services"},
        "71046": {"copay": "$15", "coinsurance": "10%", "tier": "Diagnostic Imaging"},
    }

    for code, entry in data.items():
        ext = extra.get(code, {"copay": "$0", "coinsurance": "0%", "tier": "General"})
        table_data.append([
            code,
            entry["procedure_name"],
            f"{entry['coverage_percent']}%",
            ext["copay"],
            ext["coinsurance"],
            ext["tier"],
            "Required" if entry["prior_auth_required"] else "Not Required",
        ])

    t = Table(table_data, colWidths=[55, 180, 60, 45, 65, 85, 65])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3c6e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Spacer(1, 16))
    story.append(Paragraph("Notes", styles["SectionHead"]))
    story.append(Paragraph(
        "Coverage percentages are applied after applicable copay and deductible. "
        "Procedures marked 'Prior Auth Required' must receive approval from MediGuard "
        "Utilization Management before service is rendered. Failure to obtain prior "
        "authorization may result in denial of coverage.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "MediGuard Health Plan | Document ID: COV-SCHED-2024-v3.2 | "
        "Confidential — For Provider and Member Use Only",
        styles["Footer"],
    ))

    doc.build(story)
    print(f"  Generated: policy_coverage_schedule.pdf")


# ──────────────────────────────────────────────────────────────────────
# PDF 2: Fee Schedule 2024
# ──────────────────────────────────────────────────────────────────────

def generate_fee_schedule(data: dict, output_dir: Path, styles):
    doc = SimpleDocTemplate(
        str(output_dir / "fee_schedule_2024.pdf"),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    story.append(Paragraph("MediGuard Health Plan — Fee Schedule 2024", styles["DocTitle"]))
    story.append(Paragraph("Allowed Amounts and Patient Cost-Sharing | Effective January 1, 2024", styles["BodyText2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This fee schedule establishes the maximum allowed amounts for covered procedures under "
        "the MediGuard PPO plan. Patient responsibility is calculated based on the allowed amount "
        "after application of the annual deductible ($500 individual). The out-of-pocket maximum "
        "for the 2024 plan year is $6,000 per individual and $12,000 per family.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 12))

    # Derive allowed amounts from coverage % and OOP
    # allowed_amount ≈ OOP / (1 - coverage/100) when coverage < 100
    fee_data = {
        "99213": {"allowed": 225.00, "facility": 180.00, "non_facility": 225.00},
        "99214": {"allowed": 325.00, "facility": 260.00, "non_facility": 325.00},
        "27447": {"allowed": 28333.00, "facility": 28333.00, "non_facility": 0},
        "70553": {"allowed": 2133.00, "facility": 1800.00, "non_facility": 2133.00},
        "43239": {"allowed": 1750.00, "facility": 1750.00, "non_facility": 0},
        "93000": {"allowed": 85.00, "facility": 65.00, "non_facility": 85.00},
        "90837": {"allowed": 200.00, "facility": 0, "non_facility": 200.00},
        "29881": {"allowed": 11000.00, "facility": 11000.00, "non_facility": 0},
        "36415": {"allowed": 12.00, "facility": 10.00, "non_facility": 12.00},
        "71046": {"allowed": 250.00, "facility": 200.00, "non_facility": 250.00},
    }

    story.append(Paragraph("Allowed Amounts by Procedure", styles["SectionHead"]))

    table_data = [["CPT Code", "Procedure", "Allowed Amount", "Facility Rate", "Non-Facility Rate", "Patient Responsibility"]]
    for code, entry in data.items():
        fee = fee_data.get(code, {"allowed": 0, "facility": 0, "non_facility": 0})
        table_data.append([
            code,
            entry["procedure_name"],
            f"${fee['allowed']:,.2f}",
            f"${fee['facility']:,.2f}" if fee["facility"] > 0 else "N/A",
            f"${fee['non_facility']:,.2f}" if fee["non_facility"] > 0 else "N/A",
            f"${entry['out_of_pocket_estimate']:,.2f}",
        ])

    t = Table(table_data, colWidths=[50, 170, 75, 70, 80, 90])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d5016")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0fae8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Spacer(1, 16))
    story.append(Paragraph("Payment Methodology", styles["SectionHead"]))
    story.append(Paragraph(
        "Allowed amounts are based on the Medicare Physician Fee Schedule (MPFS) with a "
        "conversion factor of 1.35x for in-network providers. Facility rates apply when "
        "services are rendered in a hospital outpatient department or ambulatory surgery "
        "center. Non-facility rates apply to physician office settings. Patient responsibility "
        "reflects estimated out-of-pocket cost after plan coverage is applied, assuming the "
        "annual deductible has been met.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "MediGuard Health Plan | Fee Schedule FY2024 | Document ID: FEE-2024-Q1-Rev2 | "
        "Not for distribution outside provider network",
        styles["Footer"],
    ))

    doc.build(story)
    print(f"  Generated: fee_schedule_2024.pdf")


# ──────────────────────────────────────────────────────────────────────
# PDF 3: Prior Authorization Guidelines
# ──────────────────────────────────────────────────────────────────────

def generate_prior_auth_guidelines(data: dict, output_dir: Path, styles):
    doc = SimpleDocTemplate(
        str(output_dir / "prior_auth_guidelines.pdf"),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    story.append(Paragraph("MediGuard Health Plan — Prior Authorization Guidelines", styles["DocTitle"]))
    story.append(Paragraph("Utilization Management Department | Updated March 2024", styles["BodyText2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "The following procedures require prior authorization before services are rendered. "
        "Failure to obtain prior authorization may result in a reduction or denial of benefits. "
        "Urgent and emergent services are exempt from prior authorization requirements. "
        "Authorization decisions are made within 5 business days for standard requests and "
        "72 hours for urgent requests.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 8))

    pa_procedures = {
        "27447": {
            "title": "CPT 27447 — Total Knee Replacement (Total Knee Arthroplasty)",
            "criteria": [
                "Patient must be 50 years of age or older, or have documented post-traumatic arthritis.",
                "Documentation of at least 6 months of conservative treatment failure, including physical therapy (minimum 12 sessions), NSAIDs or analgesic medication trial, and at least one corticosteroid injection.",
                "Radiographic evidence of moderate to severe osteoarthritis (Kellgren-Lawrence grade III or IV).",
                "Functional impairment documented by validated outcome measure (e.g., WOMAC score, KOOS).",
                "BMI must be below 45 kg/m2. Patients with BMI 40-45 require additional surgical risk assessment.",
            ],
            "docs": "Orthopedic consultation notes, imaging reports (X-ray within 6 months, MRI if available), physical therapy records, medication history, BMI documentation.",
            "turnaround": "Standard: 5 business days. Peer-to-peer review available within 48 hours of adverse determination.",
            "validity": "Authorization valid for 90 days from date of approval.",
        },
        "70553": {
            "title": "CPT 70553 — Brain MRI with and without Contrast",
            "criteria": [
                "Clinical justification required: new onset neurological symptoms (seizures, focal deficits, severe headache with red flags), suspected intracranial mass or lesion, follow-up of known intracranial pathology, or pre-surgical planning.",
                "Prior non-contrast CT or initial MRI must be documented if request is for follow-up imaging.",
                "Contrast component must be justified: suspected tumor, infection, demyelinating disease, or vascular malformation.",
                "Routine headache without red flags does not meet criteria for contrast-enhanced MRI.",
            ],
            "docs": "Ordering physician's clinical notes, prior imaging reports if applicable, neurological examination findings.",
            "turnaround": "Standard: 3 business days. Expedited review for suspected malignancy: 24 hours.",
            "validity": "Authorization valid for 60 days from date of approval.",
        },
        "29881": {
            "title": "CPT 29881 — Knee Arthroscopy with Meniscectomy",
            "criteria": [
                "MRI results must confirm meniscal tear (must be submitted with authorization request).",
                "Patient must have failed at least 6 weeks of conservative management including rest, ice, compression, physical therapy, and anti-inflammatory medication.",
                "Mechanical symptoms (locking, catching, giving way) must be documented.",
                "For patients over 50 with concomitant osteoarthritis, authorization requires documentation that the mechanical symptoms are primarily attributable to the meniscal tear.",
            ],
            "docs": "MRI report with radiologist interpretation, orthopedic evaluation notes, physical therapy records, documentation of conservative treatment timeline.",
            "turnaround": "Standard: 5 business days.",
            "validity": "Authorization valid for 60 days from date of approval.",
        },
    }

    for code, info in pa_procedures.items():
        story.append(Paragraph(info["title"], styles["SectionHead"]))

        story.append(Paragraph("<b>Clinical Criteria for Authorization:</b>", styles["BodyText2"]))
        for i, criterion in enumerate(info["criteria"], 1):
            story.append(Paragraph(f"  {i}. {criterion}", styles["BodyText2"]))
        story.append(Spacer(1, 6))

        story.append(Paragraph(f"<b>Required Documentation:</b> {info['docs']}", styles["BodyText2"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Review Turnaround:</b> {info['turnaround']}", styles["BodyText2"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Authorization Validity:</b> {info['validity']}", styles["BodyText2"]))
        story.append(Spacer(1, 12))

    story.append(Paragraph("Appeal Process", styles["SectionHead"]))
    story.append(Paragraph(
        "If a prior authorization request is denied, the requesting provider or member may "
        "submit an appeal within 180 days of the adverse determination. First-level appeals "
        "are reviewed by a physician reviewer who was not involved in the initial decision. "
        "Second-level appeals are reviewed by an external independent review organization (IRO).",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "MediGuard Health Plan | Prior Auth Guidelines | Document ID: PA-GUIDE-2024-v4.1 | "
        "For Utilization Management Use",
        styles["Footer"],
    ))

    doc.build(story)
    print(f"  Generated: prior_auth_guidelines.pdf")


# ──────────────────────────────────────────────────────────────────────
# PDF 4: Plan Benefits Summary
# ──────────────────────────────────────────────────────────────────────

def generate_plan_benefits_summary(data: dict, output_dir: Path, styles):
    doc = SimpleDocTemplate(
        str(output_dir / "plan_benefits_summary.pdf"),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    story.append(Paragraph("MediGuard Health Plan — Summary of Benefits and Coverage", styles["DocTitle"]))
    story.append(Paragraph("PPO Plan | Group Policy #MG-2024-PPO-500 | Plan Year 2024", styles["BodyText2"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Plan Overview", styles["SectionHead"]))
    story.append(Paragraph(
        "The MediGuard PPO 500 plan provides comprehensive medical coverage through a preferred "
        "provider network. Members may see any licensed provider but will receive higher benefits "
        "when using in-network providers. This summary provides an overview of your costs and "
        "coverage levels.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Cost Sharing", styles["SectionHead"]))

    cost_table = [
        ["Benefit Feature", "In-Network", "Out-of-Network"],
        ["Annual Deductible (Individual)", "$500", "$1,500"],
        ["Annual Deductible (Family)", "$1,500", "$4,500"],
        ["Out-of-Pocket Maximum (Individual)", "$6,000", "$15,000"],
        ["Out-of-Pocket Maximum (Family)", "$12,000", "$30,000"],
        ["Primary Care Office Visit Copay", "$25", "50% after deductible"],
        ["Specialist Office Visit Copay", "$40", "50% after deductible"],
        ["Emergency Room Copay", "$250 (waived if admitted)", "$250 (waived if admitted)"],
        ["Urgent Care Copay", "$50", "$50"],
    ]
    t = Table(cost_table, colWidths=[200, 130, 130])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a1a6b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f0fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Covered Services", styles["SectionHead"]))
    services = [
        ("Preventive Care", "Covered at 100% in-network with no deductible. Includes annual physicals, immunizations, and age-appropriate screenings per USPSTF guidelines."),
        ("Diagnostic Lab & Pathology", "Covered at 100% in-network (CPT 36415 venipuncture, routine panels). No prior authorization required when ordered by treating physician."),
        ("Diagnostic Imaging", "Covered at 85-90% in-network after deductible. Chest X-ray (CPT 71046) covered at 90%. Advanced imaging (MRI, CT) may require prior authorization. Brain MRI with contrast (CPT 70553) requires prior authorization and clinical justification."),
        ("Surgical Services", "Covered at 70-80% in-network after deductible. Major procedures such as total knee replacement (CPT 27447) require prior authorization and documentation of conservative treatment failure. Arthroscopic procedures (CPT 29881) require MRI confirmation."),
        ("Mental Health & Substance Abuse", "Covered under mental health parity. Outpatient psychotherapy (CPT 90837) covered at 75% with $25 copay. 30 session annual limit for outpatient psychotherapy. Inpatient mental health covered same as medical/surgical inpatient."),
        ("Cardiac Diagnostics", "ECG/EKG (CPT 93000) covered at 100% as a diagnostic procedure. No prior authorization or referral required. Stress tests and echocardiograms covered at 85% after deductible."),
        ("Gastrointestinal Procedures", "Upper GI endoscopy with biopsy (CPT 43239) covered at 90% when medically necessary. Covered under preventive benefit at 100% for age-appropriate colorectal cancer screening."),
    ]
    for title, desc in services:
        story.append(Paragraph(f"<b>{title}</b>", styles["SubHead"]))
        story.append(Paragraph(desc, styles["BodyText2"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Exclusions and Limitations", styles["SectionHead"]))
    story.append(Paragraph(
        "This plan does not cover: cosmetic surgery (unless reconstructive after injury), "
        "experimental or investigational treatments, services not medically necessary, "
        "custodial care, routine dental and vision (available as separate riders), "
        "services rendered by non-licensed providers, and charges exceeding the allowed amount "
        "for out-of-network services.",
        styles["BodyText2"],
    ))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "MediGuard Health Plan | Summary of Benefits | Document ID: SBC-2024-PPO500-v2.0 | "
        "This is a summary only. Refer to your Evidence of Coverage for complete plan details.",
        styles["Footer"],
    ))

    doc.build(story)
    print(f"  Generated: plan_benefits_summary.pdf")


# ──────────────────────────────────────────────────────────────────────
# PDF 5: Medical Policy Bulletin
# ──────────────────────────────────────────────────────────────────────

def generate_medical_policy_bulletin(data: dict, output_dir: Path, styles):
    doc = SimpleDocTemplate(
        str(output_dir / "medical_policy_bulletin.pdf"),
        pagesize=letter,
        topMargin=0.75 * inch,
        bottomMargin=0.5 * inch,
    )
    story = []

    story.append(Paragraph("MediGuard Health Plan — Medical Policy Bulletin", styles["DocTitle"]))
    story.append(Paragraph("Clinical Policy Department | Bulletin #MPB-2024-Q1 | Effective January 2024", styles["BodyText2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This bulletin provides updated medical policies and clinical criteria for select "
        "procedures. These policies supplement the Prior Authorization Guidelines and apply "
        "to all MediGuard plan products. Providers should reference this bulletin for the most "
        "current medical necessity criteria.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 8))

    policies = [
        {
            "id": "MPC-2024-ORTHO-001",
            "title": "Policy: Total Joint Replacement — Medical Necessity Criteria",
            "codes": "CPT 27447 (Total Knee Arthroplasty)",
            "content": (
                "Total knee replacement is considered medically necessary when ALL of the following "
                "criteria are met: (1) Radiographic evidence of joint space narrowing, osteophytes, "
                "or bone-on-bone articulation consistent with Kellgren-Lawrence Grade III or IV; "
                "(2) Functional limitation documented by a validated outcome score (WOMAC, KOOS, or "
                "equivalent) indicating moderate to severe impairment; (3) Failure of conservative "
                "management for a minimum of 6 months including physical therapy, pharmacological "
                "treatment, and at least one intra-articular injection; (4) Patient BMI below 45 "
                "kg/m2. Coverage: 70% of allowed amount after deductible. Estimated patient "
                "responsibility for in-network facility: $8,500. Authorization valid 90 days."
            ),
        },
        {
            "id": "MPC-2024-NEURO-003",
            "title": "Policy: Advanced Neuroimaging — Appropriate Use Criteria",
            "codes": "CPT 70553 (MRI Brain with and without Contrast)",
            "content": (
                "Brain MRI with and without contrast is considered medically necessary for: "
                "(a) New onset seizures in adults; (b) Suspected intracranial neoplasm based on "
                "clinical presentation or abnormal CT findings; (c) Monitoring of known intracranial "
                "pathology at intervals recommended by treating specialist; (d) Evaluation of "
                "demyelinating disease (e.g., multiple sclerosis); (e) Pre-operative neurosurgical "
                "planning. NOT medically necessary for: routine evaluation of chronic headache "
                "without red flags, screening in asymptomatic patients, or repeat imaging without "
                "interval change in symptoms. Coverage: 85% of allowed amount. Estimated patient "
                "out-of-pocket: $320. Prior authorization required with clinical justification."
            ),
        },
        {
            "id": "MPC-2024-ORTHO-005",
            "title": "Policy: Knee Arthroscopy — Surgical Indications",
            "codes": "CPT 29881 (Arthroscopy, Knee, Surgical; with Meniscectomy)",
            "content": (
                "Knee arthroscopy with meniscectomy is considered medically necessary when: "
                "(1) MRI confirms meniscal tear with clinical correlation; (2) Patient reports "
                "mechanical symptoms (locking, catching, giving way) for at least 6 weeks; "
                "(3) Conservative management has failed (physical therapy, NSAIDs, activity "
                "modification). Special consideration for patients over 50: when significant "
                "osteoarthritis is present on imaging, the provider must document that mechanical "
                "symptoms are primarily attributable to the meniscal pathology rather than the "
                "degenerative joint disease. Coverage: 80% of allowed amount after deductible. "
                "Estimated patient responsibility: $2,200. Prior authorization required. MRI "
                "report must be submitted with the authorization request."
            ),
        },
        {
            "id": "MPC-2024-BH-002",
            "title": "Policy: Outpatient Psychotherapy — Benefit Parameters",
            "codes": "CPT 90837 (Psychotherapy, 60 Minutes)",
            "content": (
                "Outpatient psychotherapy is covered under the mental health parity provision. "
                "60-minute individual psychotherapy sessions (CPT 90837) are covered at 75% of the "
                "allowed amount with a $25 copay per session. Annual session limit: 30 sessions per "
                "calendar year. Sessions beyond the annual limit require medical necessity review "
                "and documentation of treatment plan with measurable goals. No prior authorization "
                "required for sessions within the annual limit. Eligible provider types: licensed "
                "psychiatrists, psychologists, licensed clinical social workers (LCSW), and licensed "
                "professional counselors (LPC). Telehealth delivery is covered at the same rate as "
                "in-person visits. Estimated patient out-of-pocket per session: $50."
            ),
        },
        {
            "id": "MPC-2024-GI-001",
            "title": "Policy: Upper Gastrointestinal Endoscopy — Coverage Criteria",
            "codes": "CPT 43239 (Upper GI Endoscopy with Biopsy)",
            "content": (
                "Upper GI endoscopy with biopsy is covered at 90% of allowed amount when performed "
                "for diagnostic evaluation of: persistent dysphagia, refractory GERD (failed 8-week "
                "PPI trial), suspected Barrett's esophagus, upper GI bleeding, unexplained iron "
                "deficiency anemia, or surveillance of known Barrett's esophagus per ACG guidelines. "
                "No prior authorization required when clinical indication is documented. Estimated "
                "patient responsibility: $175. Facility-based procedure; non-facility setting not "
                "applicable. Repeat endoscopy within 12 months requires documentation of new or "
                "worsening symptoms."
            ),
        },
    ]

    for policy in policies:
        story.append(Paragraph(f"{policy['title']}", styles["SectionHead"]))
        story.append(Paragraph(f"<b>Policy ID:</b> {policy['id']}", styles["BodyText2"]))
        story.append(Paragraph(f"<b>Applicable Codes:</b> {policy['codes']}", styles["BodyText2"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(policy["content"], styles["BodyText2"]))
        story.append(Spacer(1, 12))

    story.append(Paragraph(
        "MediGuard Health Plan | Medical Policy Bulletin #MPB-2024-Q1 | "
        "Document ID: MPB-2024-Q1-v1.3 | Clinical Policy Department — Internal Use",
        styles["Footer"],
    ))

    doc.build(story)
    print(f"  Generated: medical_policy_bulletin.pdf")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = load_mock_data()
    styles = get_styles()

    print("Generating test fixture PDFs...")
    generate_policy_coverage_schedule(data, OUTPUT_DIR, styles)
    generate_fee_schedule(data, OUTPUT_DIR, styles)
    generate_prior_auth_guidelines(data, OUTPUT_DIR, styles)
    generate_plan_benefits_summary(data, OUTPUT_DIR, styles)
    generate_medical_policy_bulletin(data, OUTPUT_DIR, styles)
    print(f"\nDone! Generated 5 PDFs in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
