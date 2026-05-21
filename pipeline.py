# pipeline.py
import os
import json
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from agents import investigator
from agents import scout
from agents import drafter
from agents import auditor
import re

load_dotenv()

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage

from agents.investigator import extract_alert_entities, execute_and_serialize_graph
from agents.scout import analyze_typology_patterns
from agents.drafter import prep_str_form_fields, generate_formal_narrative
from agents.auditor import audit_generated_report

# =====================================================================
# 1. Global Multi-Agent Shared State Definition
# =====================================================================
class GlobalAgentState(TypedDict):
    messages: List[BaseMessage]
    raw_alert: Dict[str, Any]
    alert_details: Dict[str, Any]
    generated_query: str
    graph_visualization: Dict[str, Any]  # investigator -> scout/drafter
    typology_reasoning: Dict[str, Any]   # scout -> drafter/auditor
    str_form_data: Dict[str, Any]        # drafter -> auditor
    narrative_draft: str                 # drafter -> auditor
    forensic_linkages: Dict[str, str]    # drafter -> auditor
    audit_review: Dict[str, Any]         # auditor final gate


def clean_and_parse_json(raw_text: str) -> Dict[str, Any]:
    """
    Cleans raw LLM text by stripping markdown code block ticks, fixing 
    quote inconsistencies, and safely converting the string to a Python dictionary.
    """
    cleaned = raw_text.strip()
    
    # 1. Strip markdown json block wrappers if they exist
    cleaned = re.sub(re.compile(r"^```json", re.IGNORECASE), "", cleaned)
    cleaned = re.sub(re.compile(r"^```", re.IGNORECASE), "", cleaned)
    cleaned = re.sub(re.compile(r"```$", re.IGNORECASE), "", cleaned)
    cleaned = cleaned.strip()
    
    # 2. Convert single-quoted keys/values to double quotes for standard JSON compatibility
    cleaned = re.sub(r"\'(\s*[\w_]+\s*)\'\s*:", r'"\1":', cleaned)
    
    # 3. Direct attempt to parse
    try:
        return json.loads(cleaned)
    except Exception:
        # 4. Fallback: Extract everything between the outermost curly braces
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
# 2. Master Workflow Graph Assembly
# =====================================================================
master_flow = StateGraph(GlobalAgentState)

# Step A: Register Investigator Nodes

master_flow.add_node("investigator_extractor", investigator.extract_alert_entities) 
master_flow.add_node("investigator_graph_runner", investigator.execute_and_serialize_graph)

# Step B: Register Typology Scout Node
master_flow.add_node("typology_scout", scout.analyze_typology_patterns)
# Step C: Register Drafter Nodes
master_flow.add_node("drafter_data_prep", drafter.prep_str_form_fields)
master_flow.add_node("drafter_narrative_writer", drafter.generate_formal_narrative)

# Step D: Register Auditor Node
master_flow.add_node("compliance_auditor", auditor.audit_generated_report)

# =====================================================================
# 3. Defining Cross-Agent Flow Boundaries (Edges)
# =====================================================================
# Core Investigator Loop
master_flow.add_edge("investigator_extractor", "investigator_graph_runner")

# Boundary 1: Investigator pushes structured Graph JSON over to Typology Scout
master_flow.add_edge("investigator_graph_runner", "typology_scout")

# Boundary 2: Scout completes pattern analysis, routes data to Drafter's template prepper
master_flow.add_edge("typology_scout", "drafter_data_prep")
master_flow.add_edge("drafter_data_prep", "drafter_narrative_writer")

# Boundary 3: Drafter finishes narrative draft, passes package to Quality Gate Auditor
master_flow.add_edge("drafter_narrative_writer", "compliance_auditor")

# End of Pipeline: Auditor completes compliance review check and shuts down graph execution loop
master_flow.add_edge("compliance_auditor", END)

# Set global execution startup entry point node
master_flow.set_entry_point("investigator_extractor")

# Compile the multi-agent orchestration architecture into a single runtime application 
system_pipeline = master_flow.compile()

# =====================================================================
# 4. End-to-End Multi-Agent Pipeline Testing Routine
# =====================================================================
if __name__ == "__main__":
    print("🚀 Firing Up Multi-Agent SAR Investigation Pipeline...")
    
    # Simulating a real raw transaction alert arriving from your Kaggle IBM data logs!
    incoming_malicious_alert = {
        "alert_id": "ALT_2026_9981",
        "account_number": "8001002",  # Sourced target account tracking match string
        "risk_type": "High-Frequency Automated Transferred Anomalies",
        "timestamp": "2026-05-18"
    }

    initial_state_payload = {
        "messages": [],
        "raw_alert": incoming_malicious_alert,
        "alert_details": {},
        "generated_query": "",
        "graph_visualization": {},
        "typology_reasoning": {},
        "str_form_data": {},
        "narrative_draft": "",
        "forensic_linkages": {},
        "audit_review": {}
    }

    print("\nExecuting sequential worker agent loop workflow...")
    pipeline_results = system_pipeline.invoke(initial_state_payload)
    
    print("\n" + "="*80)
    print("   FINAL EXECUTED MULTI-AGENT COMPLIANCE ARCHIVE SUMMARY")
    print("="*80)
    
    print("\n[1] TYPOLOGY CONFIDENCE SCAN RESULT:")
    print(json.dumps(pipeline_results["typology_reasoning"], indent=2))
    
    print("\n[2] INTERNAL SECURITY QUALITY AUDIT REVIEW:")
    print(json.dumps(pipeline_results["audit_review"], indent=2))

    print("\n[3] FINAL COMPLIANCE NARRATIVE REPORT OUTPUT:")
    print("-" * 80)
    print(pipeline_results["narrative_draft"])
    print("-" * 80)
    
    print("\n[4] FORENSIC GRAPH INTERACTION LINKAGES MAP (FOR SPLIT-WINDOW UI):")
    print(json.dumps(pipeline_results["forensic_linkages"], indent=2))
    print("\n✅ Multi-Agent autonomous execution cycle fully finished.")