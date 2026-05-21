import os
import re
import json
import time
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

# =====================================================================
# 1. Direct Mistral Local Initialization
# =====================================================================
# GPU configs removed per your instruction. Added safe context limits.
llm = OllamaLLM(
    model="llama3.2", 
    temperature=0.1, 
    format="json",
    num_predict=2048,
    num_ctx=4096,
    additional_kwargs={"num_predict": 2048, "num_ctx": 4096}
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
    print("--- DRAFTER AGENT ACTIVATED ---")
    
    typology_json = json.dumps(state.get("typology_reasoning", {}))
    graph_json = json.dumps(state.get("graph_visualization", {}))

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert Financial Investigator drafting an FIU-IND Suspicious Transaction Report. "
            "You MUST output your response strictly as a flat JSON object. "
            "DO NOT use markdown. DO NOT use nested objects. "
            "Ensure all text is formatted cleanly without carriage returns inside strings. "
            "\n\nCRITICAL: Use EXACTLY these keys in your JSON object:"
            "\n- part_1_date: The current date (YYYY-MM-DD)"
            "\n- part_1_replacement: 'No'"
            "\n- part_2_bank: 'HDFC Bank (Simulated)'"
            "\n- part_2_officer: 'System Auto-Generated'"
            "\n- part_3_branch: 'Pune Main Branch'"
            "\n- part_4_individuals: [Array of strings listing the names of individuals found in the graph]"
            "\n- part_5_entities: [Array of strings listing merchant or ATM names found in the graph]"
            "\n- part_6_accounts: [Array of strings listing the exact raw account numbers/IDs from the graph]"
            "\n- part_7_reason: Provide a short category like 'Smurfing', 'Velocity', or 'Structuring'"
            "\n- part_7_grounds: Provide a detailed, continuous paragraph explaining the transaction flow without line breaks."
            "\n- part_8_action: 'Freeze account pending FIU-IND review'"
        )),
        ("human", "Draft the FIU-IND STR JSON using this data:\nFindings: {analytical_findings}\nGraph: {graph_json}")
    ])
    
    print("✍️ Invoking local Llama model for strict JSON drafting...")
    chain = prompt | llm
    
    ai_raw_response = chain.invoke({
        "analytical_findings": typology_json, 
        "graph_json": graph_json
    })
    
    raw_text = ai_raw_response.strip()
    
    # Strip markdown wrappers if the model ignores the prompt and hallucinates them
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3].strip()
    elif raw_text.startswith("```"):
        raw_text = raw_text[3:-3].strip()

    try:
        # Standard attempt - Because format="json" is enabled, this will almost always succeed
        report_payload = json.loads(raw_text)
        print("✅ Drafter successfully generated strict UI schema.")
    except Exception as e:
        print(f"⚠️ JSON parsing error: {e}. Falling back to default schema to prevent API crash.")
        # Failsafe so the API never crashes and the UI always renders a valid object
        report_payload = {
            "part_1_date": time.strftime("%Y-%m-%d"),
            "part_1_replacement": "No",
            "part_2_bank": "System Malfunction",
            "part_2_officer": "Error Handler",
            "part_3_branch": "Unknown",
            "part_4_individuals": ["Error retrieving individuals"],
            "part_5_entities": ["Error retrieving entities"],
            "part_6_accounts": ["Error"],
            "part_7_reason": "Data Extraction Failure",
            "part_7_grounds": f"The language model failed to return a valid JSON format. Raw output was: {raw_text[:100]}...",
            "part_8_action": "Manual review required"
        }
        
    return {
        # Store the payload as a string so the state schema (narrative_draft: str) remains unbroken for downstream agents
        "narrative_draft": json.dumps(report_payload),
        "forensic_linkages": {} # Handled natively by frontend React Flow logic now
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
    print("Initializing Drafter Agent framework using local Llama model...")
    
    mock_scout_reasoning = {
        "matched_typology": "Structuring / Smurfing Pattern Detected",
        "confidence_score": 0.94,
        "justification": "Account number ACC-7731920 received cascading sequence of automated microdeposits right below KYC alerts."
    }
    
    mock_graph_visualization = {
        "nodes": [
            {"id": "100428660", "labels": ["Account"], "properties": {"holder": "Avdhoot Patil", "status": "Flagged"}},
            {"id": "NODE_ATM_4", "labels": ["ATM"], "properties": {"location": "Pune, MH"}}
        ],
        "edges": [
            {"id": "E402", "type": "ATM_WITHDRAWAL", "source": "100428660", "target": "NODE_ATM_4", "properties": {"amount": 49500}}
        ]
    }

    initial_test_state = {
        "messages": [],
        "raw_alert": {"account_number": "100428660", "risk_type": "High-Frequency Automated Structuring"},
        "alert_details": {"account_number": "100428660", "risk_type": "High-Frequency Automated Structuring"},
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
    print("FINAL STR JSON UI PAYLOAD")
    print("=====================================================================")
    # Format the stringified JSON back into a readable dict for the terminal output
    print(json.dumps(json.loads(final_output["narrative_draft"]), indent=2))