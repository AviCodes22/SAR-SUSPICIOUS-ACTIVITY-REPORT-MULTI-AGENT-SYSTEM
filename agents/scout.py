import os
import json
from typing import Annotated, TypedDict, Dict, List,Any
from langgraph.graph import START,END,StateGraph
from langchain_core.messages import HumanMessage,AIMessage,BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import OllamaLLM
from langchain_neo4j import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_chroma import Chroma

 
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv

load_dotenv()

embeddings = OllamaEmbeddings(model="llama3")
llm = OllamaLLM(model="llama3", temperature=0.0)

graph = Neo4jGraph(
    url=os.getenv("neo4j://127.0.0.1:7687"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("Vaish@22"),
    database=os.getenv("bank-transactions")
)

vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings,
    collection_name="aml_typologies"
)

class AgentState(TypedDict):
    graph_visualization: Dict[str, Any]
    typology_reasoning: Dict[str, Any]


def analyze_typology_patterns(state: AgentState) -> Dict[str, Any]:
    graph_json_str = json.dumps(state["graph_visualization"])
    docs = vector_db.similarity_search(graph_json_str, k=2)

    typology_context = "\n\n".join([doc.page_content for doc in docs]) if docs else "No matching reference typologies found."

    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Senior Anti-Money Laundering (AML) Compliance Specialist. "
            "Analyze the provided Graph JSON network layout against the reference AML typologies context. "
            "Determine the best-matched pattern and calculate an exact confidence score between 0.00 and 1.00.\n\n"
            "Reference Typology Rules From Vector DB:\n{context}\n\n"
            "Return your final evaluation strictly as a valid JSON object matching this exact key structure:\n"
            "{{\n"
            "  'matched_typology': 'Name of pattern (e.g. Structuring, Smurfing, or None)',\n"
            "  'confidence_score': 0.92,\n"
            "  'justification': 'Detailed analytical reason mapping network nodes to the ruleset'\n"
            "}}\n"
            "Do not output markdown code formatting tags or pre-text commentaries. Only return the raw JSON object."
        )),
        ("human", "Analyze this graph network layout string: {graph_data}")
    ])
    
    chain = prompt | llm
    ai_raw_response = chain.invoke({
        "context": typology_context, 
        "graph_data": graph_json_str
    })
    
    # Safely parse out the Reasoning Object
    try:
        reasoning_object = json.loads(ai_raw_response.strip())
    except Exception:
        reasoning_object = {
            "matched_typology": "Error",
            "confidence_score": 0.00,
            "justification": f"Failed to cleanly compute structured response. Raw text: {ai_raw_response}"
        }
        
    return {
        "typology_reasoning": reasoning_object
    }