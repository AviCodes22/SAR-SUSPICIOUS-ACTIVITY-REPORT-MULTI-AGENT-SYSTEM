# agents/investigator.py
import os
import json
from typing import Annotated, TypedDict, List, Dict, Any
from dotenv import load_dotenv

load_dotenv() 

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import OllamaLLM
from langchain_neo4j import Neo4jGraph

llm = OllamaLLM(model="llama3", temperature=0.0)

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE", "bank-transactions")
)

class AgentState(TypedDict):
    messages: List[BaseMessage]
    raw_alert: Dict[str, Any]
    alert_details: Dict[str, Any]
    generated_query: str
    graph_visualization: Dict[str, Any]

# =====================================================================
# Pipeline Node Functions
# =====================================================================

def extract_alert_entities(state: AgentState) -> Dict[str, Any]:
    """
    Parses the raw text logs to pull out structured meta attributes like the 
    core target account number.
    """
    raw_payload = state.get("raw_alert", {}).get("raw_payload", "")
    account_fallback = state.get("raw_alert", {}).get("account_number", "8001002")
    
    if not raw_payload:
        # If running from master pipeline, directly pass down structured values
        return {"alert_details": {"account_number": account_fallback, "risk_type": state.get("raw_alert", {}).get("risk_type", "Velocity Anomaly")}}

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an automated AML Parser. Extract the account number and risk type from the alert text. "
            "Return strictly a valid JSON object with keys 'account_number' and 'risk_type'. No markdown tags."
        )),
        ("human", "{payload}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"payload": raw_payload}).strip()
    
    try:
        details = json.loads(response)
    except Exception:
        details = {"account_number": account_fallback, "risk_type": "Velocity Flag Anomaly"}
        
    return {"alert_details": details}


def generate_graph_query(state: AgentState) -> Dict[str, Any]:
    """
    Uses AI to generate a dynamic Cypher query to pull a graph neighborhood.
    """
    account_number = state["alert_details"].get("account_number", "8001002")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert Neo4j Database Engineer. Generate a Cypher query that finds an "
            "(:Account) node matching the parameter $account_number, performs a 2-hop traversal "
            "to capture transaction paths, and returns the path data. "
            "Return ONLY the raw Cypher query text. No markdown formatting code block tags."
        )),
        ("human", "Generate a query for account number parameter.")
    ])
    
    chain = prompt | llm
    generated_cypher = chain.invoke({}).strip()
    
    # Fallback to a solid boilerplate query if Llama3 defaults to conversational chat text
    if "MATCH" not in generated_cypher:
        generated_cypher = "MATCH (a:Account {id: $account_number})-[r:TRANSFERRED]->(b:Account) RETURN a, r, b LIMIT 10"

    return {"generated_query": generated_cypher}


def execute_and_serialize_graph(state: dict) -> dict:
    from langchain_community.graphs import Neo4jGraph
    import os
    
    # 1. Get the target account
    account_number = state.get("raw_alert", {}).get("account_number", "")
    print(f"🔍 Investigator Agent querying Neo4j for Account: {account_number}")

    # 2. Connect to DB
    graph = Neo4jGraph(
        url=os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
        username=os.getenv("NEO4J_USERNAME", "neo4j"),
        password=os.getenv("NEO4J_PASSWORD", "your_secure_password")
    )

    # 3. The REAL IBM Dataset Cypher Query
    query = """
    MATCH (a:Account {id: $account_id})-[r:TRANSFERRED]->(b:Account)
    RETURN a.id AS sender, r.amount AS amount, r.is_laundering AS is_laundering, b.id AS receiver, r.timestamp AS time
    LIMIT 25
    """
    
    results = graph.query(query, params={"account_id": str(account_number)})
    
    if not results:
        print(f"❌ FATAL: Account {account_number} not found in Neo4j! Did you seed the DB?")
        return {"graph_visualization": {"nodes": [], "edges": []}}

    # 4. Serialize real data for the React UI
    nodes_payload = []
    edges_payload = []
    seen_nodes = set()

    for i, record in enumerate(results):
        sender = record["sender"]
        receiver = record["receiver"]
        
        if sender not in seen_nodes:
            nodes_payload.append({"id": sender, "labels": ["Account"], "properties": {"id": sender}})
            seen_nodes.add(sender)
        if receiver not in seen_nodes:
            nodes_payload.append({"id": receiver, "labels": ["Account"], "properties": {"id": receiver}})
            seen_nodes.add(receiver)
            
        edges_payload.append({
            "id": f"E{i}", 
            "type": "TRANSFERRED", 
            "source": sender, 
            "target": receiver, 
            "properties": {"amount": record["amount"], "is_laundering": record["is_laundering"]}
        })

    print(f"✅ Extracted {len(nodes_payload)} real nodes and {len(edges_payload)} real edges.")
    
    return {
        "graph_visualization": {
            "nodes": nodes_payload,
            "edges": edges_payload
        }
    }

# =====================================================================
# LangGraph Workflow Construction
# =====================================================================
workflow = StateGraph(AgentState)

workflow.add_node("entity_extractor", extract_alert_entities)
workflow.add_node("query_generator", generate_graph_query)
workflow.add_node("graph_executor", execute_and_serialize_graph)

workflow.add_edge("entity_extractor", "query_generator")
workflow.add_edge("query_generator", "graph_executor")
workflow.add_edge("graph_executor", END)

workflow.set_entry_point("entity_extractor")
investigator_agent = workflow.compile()

if __name__ == "__main__":
    mock_alert = {
      "alert_id": "ALRT-2026-99482",
      "raw_payload": "CRITICAL: Velocity check failed tracking account number: ACC-7731920. Pattern flag: Structuring."
    }
    print("Running Standalone Investigator Agent Test...")
    final_output = investigator_agent.invoke({"messages": [], "raw_alert": mock_alert, "alert_details": {}, "generated_query": "", "graph_visualization": {}})
    print(json.dumps(final_output["graph_visualization"], indent=2))