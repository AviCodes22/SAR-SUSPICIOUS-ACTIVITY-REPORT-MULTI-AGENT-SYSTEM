import os
import re
import json
import time
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

# Load configurations from your .env file
load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM

# =====================================================================
# 1. Direct Mistral Local Initialization
# =====================================================================
llm = OllamaLLM(
    model="llama3.2", 
    temperature=0.1, 
    format="json",
    num_gpu=-1 
)
# =====================================================================
# 2. Unified Multi-Agent State Definition
# =====================================================================
class AgentState(TypedDict):
    messages: List[BaseMessage]
    raw_alert: Dict[str, Any]
    alert_details: Dict[str, Any]
    generated_query: str
    graph_visualization: Dict[str, Any]
    typology_reasoning: Dict[str, Any]
    str_form_data: Dict[str, Any]
    narrative_draft: str
    forensic_linkages: Dict[str, str]

def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    cleaned = raw_text.strip()
    
    cleaned = re.sub(re.compile(r"^```json", re.IGNORECASE), "", cleaned)
    cleaned = re.sub(re.compile(r"^```", re.IGNORECASE), "", cleaned)
    cleaned = re.sub(re.compile(r"```$", re.IGNORECASE), "", cleaned)
    cleaned = cleaned.strip()
    
    cleaned = re.sub(r"\'(\s*[\w_]+\s*)\'\s*:", r'"\1":', cleaned)
    cleaned = cleaned.replace("\n", " ").replace("\r", "")
    
    try:
        return json.loads(cleaned)
    except Exception:
        try:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
            
        return {
            "error_parsing": True,
            "raw_output": raw_text
        }

# =====================================================================
# 3. Agent Processing Node Definitions
# =====================================================================
def prep_str_form_fields(state: AgentState) -> Dict[str, Any]:
    alert_details = state.get("alert_details", {})
    graph_visualization = state.get("graph_visualization", {})
    
    target_account_id = alert_details.get("account_number", "UNKNOWN")
    detected_reason = alert_details.get("risk_type", "Velocity Flag")
    
    nodes = graph_visualization.get("nodes", [])
    account_holder_name = "UNKNOWN HOLDER"
    if nodes:
        account_holder_name = nodes[0].get("properties", {}).get("holder", "UNKNOWN HOLDER")
    
    str_form_payload = {
        "fi_name": "SAR MULTI_AGENT_SYSTEM BANK",
        "fi_branch_id": "LOC_PUNE_VIT_01",
        "date_of_report": time.strftime("%Y-%m-%d"),
        "subject_account_id": target_account_id,
        "subject_name": account_holder_name,
        "suspicion_reason_primary": detected_reason,
        "first_txn_date": "2026-01-10",
        "last_txn_date": time.strftime("%Y-%m-%d"),
        "total_value_inr": 1250000
    }
    
    return {
        "str_form_data": str_form_payload
    }


def generate_formal_narrative(state: AgentState) -> Dict[str, Any]:
    # --- EXTRACT DATA FROM STATE ---
    typology_json = json.dumps(state.get("typology_reasoning", {}))
    graph_json = json.dumps(state.get("graph_visualization", {}))

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Lead AML Compliance Officer at an Indian Bank. Your job is to draft an official "
            "FIU-IND Suspicious Transaction Report (STR). "
            "You MUST output your response strictly as a JSON object with 'narrative' and 'forensic_linkages' keys. "
            "\n\nCRITICAL NARRATIVE FORMATTING RULES: "
            "\n1. You MUST use Markdown headers (###) for every part of the form."
            "\n2. DO NOT write paragraphs where lists are required."
            "\n\nSTRUCTURE THE REPORT EXACTLY LIKE THIS FIU-IND STR FORM:"
            "\n### PART 1: DETAILS OF REPORT"
            "\n- Date of sending report: [Current Date]"
            "\n- Is this a replacement report?: No"
            "\n\n### PART 2 & 3: PRINCIPAL OFFICER & BRANCH"
            "\n- Name of Bank: HDFC Bank (Simulated)"
            "\n- Name of Principal Officer: System Auto-Generated"
            "\n- Branch: Pune Main Branch"
            "\n\n### PART 4 & 5: LIST OF INDIVIDUALS / ENTITIES LINKED TO TRANSACTIONS"
            "\n[List the names and roles of the nodes found in the graph]"
            "\n\n### PART 6: LIST OF ACCOUNTS"
            "\n[List the specific Account IDs from the graph]"
            "\n\n### PART 7: DETAILS OF SUSPICIOUS TRANSACTION"
            "\n**7.1 Reasons for suspicion:** [State the RAG typology match, e.g., Value of transaction, Activity in account, etc.]"
            "\n**7.2 Grounds of Suspicion:** [Write a clear, simple 2-paragraph explanation of how the suspect is moving the money, avoiding jargon. Explain the crime.]"
            "\n\n### PART 8: DETAILS OF ACTION TAKEN"
            "\n[Write the final recommendation, e.g., Freeze account pending FIU-IND review]"
        )),
        ("human", "Write the FIU-IND STR using this data:\nFindings: {analytical_findings}\nGraph: {graph_json}")
    ])
    
    # --- EXECUTE THE LLM ---
    print("✍️ Invoking local Llama model via GPU...")
    chain = prompt | llm
    
    # Store the result directly into ai_raw_response
    ai_raw_response = chain.invoke({
        "analytical_findings": typology_json, 
        "graph_json": graph_json
    })
    
    # --- UPGRADED ROBUST PARSING LOGIC ---
    raw_text = ai_raw_response.strip()
    
    # Clean up outer markdown block wrappers if present
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()

    try:
        # Standard attempt
        report_payload = json.loads(raw_text)
        print("✅ Drafter successfully parsed compliance report JSON object.")
    except Exception:
        try:
            # Secondary repair: Escape real carriage breaks that break JSON tokenization
            fixed_raw = raw_text.replace("\n", "\\n").replace("\r", "\\r")
            fixed_raw = fixed_raw.replace("\\\\n", "\\n")
            
            # Isolate the core JSON braces if surrounding text exists
            match = re.search(r"\{.*\}", fixed_raw, re.DOTALL)
            if match:
                report_payload = json.loads(match.group(0))
            else:
                raise ValueError("No JSON boundaries found.")
        except Exception as fallback_err:
            print(f"⚠️ Defensive regex patch engaged due to complex string formatting: {fallback_err}")
            
            # Direct text extraction backup: If it contains structural markers, use the text natively!
            clean_narrative = raw_text
            if '"narrative"' in raw_text:
                try:
                    start_idx = raw_text.find('"narrative"') + 11
                    while raw_text[start_idx] in [':', ' ', '"', '\n']:
                        start_idx += 1
                    end_idx = raw_text.find('"forensic_linkages"')
                    if end_idx != -1:
                        clean_narrative = raw_text[start_idx:end_idx].strip().rstrip(',').rstrip('"').strip()
                except Exception:
                    pass
            
            report_payload = {
                "narrative": clean_narrative,
                "forensic_linkages": {"100428660": "PART 6"}
            }
        
    return {
        "narrative_draft": report_payload.get("narrative", raw_text).replace("\\n", "\n"),
        "forensic_linkages": report_payload.get("forensic_linkages", {})
    }

# =====================================================================
# 4. State Machine Workflow Construction
# =====================================================================
drafter_workflow = StateGraph(AgentState)

drafter_workflow.add_node("data_prep", prep_str_form_fields)
drafter_workflow.add_node("narrative_drafter", generate_formal_narrative)

drafter_workflow.add_edge("data_prep", "narrative_drafter")
drafter_workflow.add_edge("narrative_drafter", END)

drafter_workflow.set_entry_point("data_prep")

drafter_agent = drafter_workflow.compile()

# =====================================================================
# 5. Local Standalone Test Verification Execution
# =====================================================================
if __name__ == "__main__":
    print("Initializing Drafter Agent framework using local Mistral model...")
    
    mock_scout_reasoning = {
        "matched_typology": "Structuring / Smurfing Pattern Detected",
        "confidence_score": 0.94,
        "justification": "Account number ACC-7731920 received cascading sequence of automated microdeposits right below KYC alerts."
    }
    
    mock_graph_visualization = {
        "nodes": [
            {"id": "ACC-7731920", "labels": ["Account"], "properties": {"holder": "Avdhoot Patil", "status": "Flagged"}},
            {"id": "NODE_ATM_4", "labels": ["ATM"], "properties": {"location": "Pune, MH"}}
        ],
        "edges": [
            {"id": "E402", "type": "ATM_WITHDRAWAL", "source": "ACC-7731920", "target": "NODE_ATM_4", "properties": {"amount": 49500}}
        ]
    }

    initial_test_state = {
        "messages": [],
        "raw_alert": {"account_number": "ACC-7731920", "risk_type": "High-Frequency Automated Structuring"},
        "alert_details": {"account_number": "ACC-7731920", "risk_type": "High-Frequency Automated Structuring"},
        "generated_query": "MATCH paths... RETURN lists",
        "graph_visualization": mock_graph_visualization,
        "typology_reasoning": mock_scout_reasoning,
        "str_form_data": {},
        "narrative_draft": "",
        "forensic_linkages": {}
    }

    print("\nExecuting Drafter Workflow Pipeline...")
    final_output = drafter_agent.invoke(initial_test_state)
    
    print("\n=====================================================================")
    print("STRUCTURED FORM METADATA GENERATION")
    print("=====================================================================")
    print(json.dumps(final_output["str_form_data"], indent=2))
    
    print("\n=====================================================================")
    print("FORENSIC UI HOVER LINKAGES MAP")
    print("=====================================================================")
    print(json.dumps(final_output["forensic_linkages"], indent=2))

    print("\n=====================================================================")
    print("FINAL 5-PARAGRAPH SUSPICIOUS TRANSACTION REPORT NARRATIVE DRAFT")
    print("=====================================================================")
    print(final_output["narrative_draft"])