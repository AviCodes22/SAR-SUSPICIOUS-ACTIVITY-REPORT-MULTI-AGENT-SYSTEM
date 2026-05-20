# data_ingestion/seed_chroma.py
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document

load_dotenv()

# Use local Llama3 embeddings matching your local Ollama runtime setup
embeddings = OllamaEmbeddings(model="llama3")

# Initialize ChromaDB connection target folder 
vector_db = Chroma(
    persist_directory="./chroma_db", 
    embedding_function=embeddings,
    collection_name="aml_typologies"
)

def seed_typology_kb():
    """
    Seeds ChromaDB with explicit compliance documentation parameters 
    defining known international AML/CFT transaction typologies.
    """
    typologies = [
        Document(
            page_content=(
                "Typology: High-Frequency Structuring (Smurfing). "
                "The practice of executing a series of financial transactions in small amounts "
                "specifically designed to fall under anti-money laundering reporting thresholds "
                "(e.g., splitting a 2,000,000 INR deposit into multiple transactions under 50,000 INR). "
                "Look for rapid cash bursts or multiple structured inputs converging on a single target node."
            ),
            metadata={"category": "Structuring", "severity": "High"}
        ),
        Document(
            page_content=(
                "Typology: Rapid Funds Routing (Layering). "
                "Funds are transferred into an account and immediately moved out to secondary "
                "entities or shell accounts within a tight temporal window. The account acts purely "
                "as a pass-through node, maintaining a near-zero closing balance despite high total value volume."
            ),
            metadata={"category": "Layering", "severity": "Critical"}
        ),
        Document(
            page_content=(
                "Typology: Mule Integration Loop (Fan-In / Fan-Out). "
                "A network topology where multiple unlinked sender nodes route funds to a single central "
                "consolidation point account. This consolidation account then splits and routes the aggregate sum "
                "outward to high-risk offshore channels or ATM withdrawal terminals."
            ),
            metadata={"category": "Mule Network", "severity": "High"}
        )
    ]
    
    print("Populating local ChromaDB collection reference data...")
    vector_db.add_documents(typologies)
    print("✅ ChromaDB knowledge base successfully seeded!")

if __name__ == "__main__":
    seed_typology_kb()