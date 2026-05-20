# data_ingestion/seed_neo4j.py
import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Setup database driver connection parameters from your core .env file
URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
USER = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD")
DATABASE = os.getenv("NEO4J_DATABASE", "bank-transactions")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def ingest_kaggle_aml_data(csv_path: str, row_limit: int = 5000):
    """
    Parses structural financial rows from the Kaggle AML dataset 
    and injects them as linked graph components into Neo4j.
    """
    if not os.path.exists(csv_path):
        print(f"❌ Error: Could not find the file at {csv_path}. Please check your path configuration.")
        return

    print(f"Reading first {row_limit} lines from Kaggle AML dataset...")
    df = pd.read_csv(csv_path, nrows=row_limit)
    
    # Standardize column naming formatting properties to prevent string dictionary escaping syntax errors
    df.columns = df.columns.str.strip().str.replace('.', '_', regex=False)

    # Cypher query optimizing node merges and edge properties mapping execution batches
    cypher_query = """
    UNWIND $rows AS row
    MERGE (source:Account {id: toString(row.Account)})
    ON CREATE SET source.bank = row.From_Bank
    
    MERGE (target:Account {id: toString(row.Account_1})
    ON CREATE SET target.bank = row.To_Bank
    
    CREATE (source)-[tx:TRANSFERRED {
        timestamp: row.Timestamp,
        amount: toFloat(row.Amount_Received),
        currency: row.Receiving_Currency,
        format: row.Payment_Format,
        is_laundering: toInteger(row.Is_Laundering)
    }]->(target)
    """
    
    records_payload = df.to_dict(orient='records')
    
    print(f"Connecting to database '{DATABASE}' and injecting graph topology paths...")
    with driver.session(database=DATABASE) as session:
        # Enforce uniqueness constraint to maximize query path lookup processing speed
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Account) REQUIRE a.id IS UNIQUE")
        
        # Batch execute transactional node mapping blocks
        session.run(cypher_query, rows=records_payload)
        
    print("✅ Neo4j graph dataset successfully built!")

if __name__ == "__main__":
    # Update this file location path string to match your computer layout folder download target
    TARGET_KAGGLE_CSV = "d:/EDAI SEM 4/datasets/HI-Small_Trans.csv"
    ingest_kaggle_aml_data(TARGET_KAGGLE_CSV, row_limit=5000)