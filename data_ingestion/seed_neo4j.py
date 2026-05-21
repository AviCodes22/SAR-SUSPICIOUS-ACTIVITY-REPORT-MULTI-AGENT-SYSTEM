# data_ingestion/seed_neo4j.py
import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Setup Neo4j connection
URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "your_secure_password") # Make sure this matches your DB password!

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

CSV_PATH = "HI-Small_Trans.csv"

def seed_graph_database():
    print("🚀 Loading IBM HI-Small_Trans.csv into Pandas...")
    
    # Read the CSV. Pandas automatically renames duplicate columns (Account -> Account.1)
    df = pd.read_csv(CSV_PATH)
    
    # For testing, let's just take the first 5,000 rows so it loads fast on your laptop
    df = df.head(5000)
    
    print(f"✅ Loaded {len(df)} transactions. Pushing to Neo4j...")

    with driver.session() as session:
        # 1. Clear existing database to start fresh
        session.run("MATCH (n) DETACH DELETE n")
        
        # 2. Iterate through dataframe and create nodes/edges
        for index, row in df.iterrows():
            sender_id = str(row['Account'])
            receiver_id = str(row['Account.1'])
            amount = float(row['Amount Paid'])
            is_laundering = int(row['Is Laundering'])
            
            # Cypher query to create the structural map
            cypher_query = """
            MERGE (sender:Account {id: $sender_id})
            MERGE (receiver:Account {id: $receiver_id})
            CREATE (sender)-[r:TRANSFERRED {
                amount: $amount,
                is_laundering: $is_laundering,
                currency: $currency,
                timestamp: $timestamp
            }]->(receiver)
            """
            
            session.run(cypher_query, 
                        sender_id=sender_id, 
                        receiver_id=receiver_id,
                        amount=amount,
                        is_laundering=is_laundering,
                        currency=row['Payment Currency'],
                        timestamp=row['Timestamp'])
            
            if index % 500 == 0 and index > 0:
                print(f"Processed {index} transactions...")

    print("🏁 Neo4j Seeding Complete! The graph is now live.")

if __name__ == "__main__":
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: Could not find {CSV_PATH} in the root directory.")
    else:
        seed_graph_database()