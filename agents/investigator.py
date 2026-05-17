import json
from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.llms import Ollama 
from langchain_community.vectorstores import Neo4jVector
from langchain_community.graphs import Neo4jGraph
from dotenv import load_dotenv
load_dotenv() 


llm = Ollama(model="llama3", temperature=0.0)
graph = Neo4jGraph()


class AgentState(TypedDict):
    messages: List[BaseMessage]
    raw_alert: Dict[str, Any]
    alert_details: Dict[str, Any]
    generated_query: str
    graph_visualization: Dict[str, Any]


def extract_alert_entities(state: AgentState) -> Dict[str, Any]:
    """
    Uses AI to dynamically parse the raw alert text and accurately isolate the 
    underlying account number and event type.
    """
    raw_alert_str = json.dumps(state["raw_alert"])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an elite cyber-forensics parser. Analyze the incoming banking alert payload "
            "and extract the core subject account number. "
            "Return your answer as a valid JSON object with exactly two keys: 'account_number' and 'risk_type'. "
            "Do not include any code blocks, commentary, or extra text. Only return the raw JSON object."
        )),
        ("human", "Analyze this alert payload: {payload}")
    ])
    
    chain = prompt | llm
    ai_response = chain.invoke({"payload": raw_alert_str})
    
    try:
        extracted_details = json.loads(ai_response.strip())
    except Exception:
        extracted_details = {"account_number": "UNKNOWN", "risk_type": "Unknown"}
        
    return {
        "alert_details": extracted_details
    }


def generate_graph_query(state: AgentState) -> Dict[str, Any]:
    """
    Uses AI to generate a dynamic Cypher query to pull a 2-hop graph neighborhood
    around the extracted account number, capturing KYC details, history, and transactions.
    """
    account_number = state["alert_details"].get("account_number", "")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert Neo4j Database Engineer. Generate a Cypher query that finds an "
            "(:Account) node matching the provided account number, performs a 2-hop traversal "
            "([*1..2]) to capture all connected transaction paths, KYC data, and historical case logs. "
            "Your output format MUST collect unique nodes and unique edges and return them as two distinct lists. "
            "Return ONLY the raw Cypher query text. No explanations, no markdown formatting blocks."
        )),
        ("human", "Generate a query for account number: '{account_number}'")
    ])
    
    chain = prompt | llm
    generated_cypher = chain.invoke({"account_number": account_number})
    
    return {
        "generated_query": generated_cypher.strip()
    }


def execute_and_serialize_graph(state: AgentState) -> Dict[str, Any]:
    """
    Executes the AI-generated Cypher query on Neo4j and transforms the dataset
    into a clean Graph JSON structure optimized for UI visualization frameworks.
    """
    query = state["generated_query"]
    account_number = state["alert_details"].get("account_number", "")
    
    results = graph.query(query, {"account_number": account_number})
    
    nodes_payload = results[0].get("nodes", []) if results else []
    edges_payload = results[0].get("edges", []) if results else []
    
    structured_graph_json = {
        "nodes": nodes_payload,
        "edges": edges_payload
    }
    
    return {
        "graph_visualization": structured_graph_json
    }


workflow = StateGraph(AgentState)


workflow.add_node("entity_extractor", extract_alert_entities)
workflow.add_node("query_generator", generate_graph_query)
workflow.add_node("graph_executor", execute_and_serialize_graph)


workflow.add_edge("entity_extractor", "query_generator")
workflow.add_edge("query_generator", "graph_executor")
workflow.add_edge("graph_executor", END)


workflow.set_entry_point("entity_extractor")


investigator_agent = workflow.compile()

#TEST DATA:
if __name__ == "__main__":
    mock_alert = {
      "alert_id": "ALRT-2026-99482",
      "source": "CoreBanking_Flag_Service",
      "raw_payload": "CRITICAL: Velocity check failed for terminal Txn_Ref_88192. Node point localized to customer routing ledger tracking account number: ACC-7731920. Pattern flag: Structuring/High-frequency automated transfers detected."
    }

    initial_state = {
        "messages": [],
        "raw_alert": mock_alert,
        "alert_details": {},
        "generated_query": "",
        "graph_visualization": {}
    }

    print("Running Investigator Agent...")
    final_output = investigator_agent.invoke(initial_state)

    print("\n--- Final Graph JSON Result for UI Visualization ---")
    print(json.dumps(final_output["graph_visualization"], indent=2))