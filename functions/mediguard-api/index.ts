// MedGuardAI API Edge Function
// Handles: /api/health, /api/procedures, /api/demo, /api/insurance/{code}, /api/visits

/// <reference lib="deno.ns" />

import { createClient } from 'npm:@insforge/sdk@latest';

// Mock insurance data (embedded for edge function)
const INSURANCE_DATA: Record<string, any> = {
  "99213": {
    "procedure_name": "Office Visit (Established Patient, Moderate Complexity)",
    "coverage_percent": 80,
    "out_of_pocket_estimate": 45.00,
    "prior_auth_required": false,
    "notes": "Standard copay applies. No referral needed."
  },
  "99214": {
    "procedure_name": "Office Visit (Established Patient, High Complexity)",
    "coverage_percent": 80,
    "out_of_pocket_estimate": 65.00,
    "prior_auth_required": false,
    "notes": "Standard copay applies. No referral needed."
  },
  "27447": {
    "procedure_name": "Total Knee Replacement",
    "coverage_percent": 70,
    "out_of_pocket_estimate": 8500.00,
    "prior_auth_required": true,
    "notes": "Prior authorization required. Must demonstrate 6 months of conservative treatment failure."
  },
  "70553": {
    "procedure_name": "Brain MRI with and without Contrast",
    "coverage_percent": 85,
    "out_of_pocket_estimate": 320.00,
    "prior_auth_required": true,
    "notes": "Prior authorization required. Clinical justification must accompany request."
  },
  "43239": {
    "procedure_name": "Upper GI Endoscopy with Biopsy",
    "coverage_percent": 90,
    "out_of_pocket_estimate": 175.00,
    "prior_auth_required": false,
    "notes": "Covered under preventive/diagnostic benefit when medically necessary."
  },
  "93000": {
    "procedure_name": "Electrocardiogram (ECG/EKG), 12-Lead",
    "coverage_percent": 100,
    "out_of_pocket_estimate": 0.00,
    "prior_auth_required": false,
    "notes": "Fully covered as diagnostic procedure."
  },
  "90837": {
    "procedure_name": "Psychotherapy, 60 Minutes",
    "coverage_percent": 75,
    "out_of_pocket_estimate": 50.00,
    "prior_auth_required": false,
    "notes": "Mental health parity applies. 30 sessions/year limit."
  },
  "29881": {
    "procedure_name": "Knee Arthroscopy with Meniscectomy",
    "coverage_percent": 80,
    "out_of_pocket_estimate": 2200.00,
    "prior_auth_required": true,
    "notes": "Prior authorization required. MRI results must be submitted."
  },
  "36415": {
    "procedure_name": "Routine Venipuncture (Blood Draw)",
    "coverage_percent": 100,
    "out_of_pocket_estimate": 0.00,
    "prior_auth_required": false,
    "notes": "Fully covered when ordered by treating physician."
  },
  "71046": {
    "procedure_name": "Chest X-Ray, 2 Views",
    "coverage_percent": 90,
    "out_of_pocket_estimate": 25.00,
    "prior_auth_required": false,
    "notes": "Covered under diagnostic imaging benefit."
  },
  "72148": {
    "procedure_name": "MRI Lumbar Spine without Contrast",
    "coverage_percent": 80,
    "out_of_pocket_estimate": 400.00,
    "prior_auth_required": false,
    "notes": "No prior authorization required for diagnostic imaging of lumbar spine."
  }
};

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization'
};

function getInsuranceQuote(procedureCode: string, patientId: string = "default") {
  const data = INSURANCE_DATA[procedureCode];
  if (!data) {
    return {
      procedure_code: procedureCode,
      procedure_name: "Unknown Procedure",
      coverage_percent: 0,
      out_of_pocket_estimate: 0,
      prior_auth_required: true,
      notes: `Procedure code '${procedureCode}' not found in coverage database.`
    };
  }
  return {
    procedure_code: procedureCode,
    ...data
  };
}

function listAvailableProcedures() {
  return Object.entries(INSURANCE_DATA).map(([code, data]) => ({
    code,
    name: data.procedure_name
  }));
}

async function runOrchestrator(request: any) {
  const { doctor_notes, procedure_code, patient_id } = request;
  
  // Step 1: Get insurance quote
  const insuranceQuote = getInsuranceQuote(procedure_code, patient_id);
  
  // Step 2: Generate patient summary
  const patientSummary = {
    summary: `Your doctor has ordered ${insuranceQuote.procedure_name.toLowerCase()}. ${insuranceQuote.notes} Your insurance covers ${insuranceQuote.coverage_percent}% after deductible, leaving you with approximately $${insuranceQuote.out_of_pocket_estimate.toFixed(2)} out-of-pocket.${insuranceQuote.prior_auth_required ? ' Prior authorization is required, which we will help you obtain.' : ''}`,
    key_points: [
      `${insuranceQuote.procedure_name} - medically necessary procedure`,
      `Insurance covers ${insuranceQuote.coverage_percent}% after deductible`,
      `Your estimated cost: $${insuranceQuote.out_of_pocket_estimate.toFixed(2)}`,
      insuranceQuote.prior_auth_required ? "Prior authorization needed - we'll handle this" : "No prior authorization required",
      "Follow your doctor's pre-procedure instructions"
    ]
  };
  
  // Step 3: Build agent trace
  const now = new Date();
  const agentTrace = [
    {
      agent_name: "Orchestrator",
      action: "Received doctor request",
      input_summary: `Procedure: ${procedure_code}, Patient: ${patient_id}`,
      output_summary: "Routing to Insurance Agent",
      timestamp: now.toISOString()
    },
    {
      agent_name: "Insurance Agent",
      action: "Retrieved coverage details",
      input_summary: `Lookup CPT code ${procedure_code}`,
      output_summary: `${insuranceQuote.coverage_percent}% coverage, prior auth ${insuranceQuote.prior_auth_required ? 'required' : 'not required'}`,
      timestamp: new Date(now.getTime() + 500).toISOString()
    },
    {
      agent_name: "Patient Agent",
      action: "Generated explanation",
      input_summary: "Insurance quote details",
      output_summary: "Plain-language summary created",
      timestamp: new Date(now.getTime() + 1000).toISOString()
    }
  ];
  
  return {
    insurance_quote: insuranceQuote,
    patient_summary: patientSummary,
    agent_trace: agentTrace
  };
}

export default async function(req: Request): Promise<Response> {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  const url = new URL(req.url);
  const path = url.pathname;

  try {
    // Health check
    if (path === '/api/health' && req.method === 'GET') {
      return new Response(JSON.stringify({ status: "healthy", service: "MediGuardAI" }), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // List procedures
    if (path === '/api/procedures' && req.method === 'GET') {
      return new Response(JSON.stringify(listAvailableProcedures()), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Get insurance quote
    const insuranceMatch = path.match(/^\/api\/insurance\/(.+)$/);
    if (insuranceMatch && req.method === 'GET') {
      const procedureCode = insuranceMatch[1];
      const patientId = url.searchParams.get('patient_id') || 'default';
      const quote = getInsuranceQuote(procedureCode, patientId);
      return new Response(JSON.stringify(quote), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Run demo
    if (path === '/api/demo' && req.method === 'POST') {
      const body = await req.json();
      const result = await runOrchestrator(body);
      return new Response(JSON.stringify(result), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Get patient visits
    if (path === '/api/visits' && req.method === 'GET') {
      const patientId = url.searchParams.get('patient_id');
      if (!patientId) {
        return new Response(JSON.stringify({ error: "patient_id required" }), {
          status: 400,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      // Query database for patient visits
      const client = createClient({
        baseUrl: Deno.env.get('INSFORGE_BASE_URL') || 'https://em6x2e4c.us-east.insforge.app',
        edgeFunctionToken: Deno.env.get('INSFORGE_API_KEY')
      });
      
      const { data, error } = await client.database
        .from('patient_visits')
        .select('*')
        .eq('patient_id', patientId)
        .order('visit_date', { ascending: false });
      
      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(data), {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Create patient visit (when doctor submits)
    if (path === '/api/visits' && req.method === 'POST') {
      const body = await req.json();
      const { patient_id, doctor_id, procedure_code, diagnosis, release_notes } = body;
      
      const client = createClient({
        baseUrl: Deno.env.get('INSFORGE_BASE_URL') || 'https://em6x2e4c.us-east.insforge.app',
        edgeFunctionToken: Deno.env.get('INSFORGE_API_KEY')
      });
      
      const { data, error } = await client.database
        .from('patient_visits')
        .insert([{
          patient_id,
          doctor_id,
          procedure_code,
          diagnosis,
          release_notes,
          visit_date: new Date().toISOString()
        }])
        .select();
      
      if (error) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' }
        });
      }
      
      return new Response(JSON.stringify(data), {
        status: 201,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Not found
    return new Response(JSON.stringify({ error: "Not found" }), {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error: any) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
}
