# 🏦 SAR Autonomous Intelligence Unit (Multi-Agent RAG System)

An enterprise-grade, multi-agent AI system built with **LangGraph**, **FastAPI**, **Neo4j**, and **ChromaDB**. This system automates the investigation and drafting of Suspicious Activity Reports (SARs) for financial institutions, drastically reducing compliance review times from hours to seconds.

---

## 🏃‍♂️ Running the System

1. Seed the Vector Database (ChromaDB):
Before running the pipeline, initialize the local RAG knowledge base containing AML compliance laws.

```bash
python data_ingestion/seed_chroma.py
```
2. Start the FastAPI Server:
Boot up the backend microservice to expose the /api/investigate endpoint.

```bash
python api.py
```

The API will now be live at http://localhost:8000. You can visit http://localhost:8000/docs to test the API directly using Swagger UI.

---

## System Architecture & Workflow

The backend operates as a sequential StateGraph, utilizing 4 specialized AI agents working autonomously:

1. **Investigator Agent:** Ingests the raw banking alert, extracts entity data, queries a **Neo4j** graph database, and outputs a structured `Graph JSON` tracking the flow of funds.
2. **Typology Scout Agent (RAG):** Takes the graph data and searches a **ChromaDB** vector database containing international financial crime rules (FATF, RBI, FIU). It calculates a confidence score matching the activity to a specific crime (e.g., Smurfing, Layering).
3. **Drafter Agent:** Uses LLMs (Llama3/Mistral) to synthesize the graph data and Scout findings into a formal, highly accurate 5-paragraph SAR narrative.
4. **Auditor Agent:** Acts as an internal QA layer. It strictly verifies the drafted narrative against the raw data to ensure zero AI hallucinations before final approval.

---

## Input & Output Showcase

### 1. The Trigger (Input Mock Alert)
The system is activated by a standard JSON payload from a core banking system:
```json
{
  "alert_id": "ALRT-2026-99482",
  "source": "CoreBanking_Flag_Service",
  "timestamp": "2026-05-18T00:45:12Z",
  "raw_payload": "CRITICAL: Velocity check failed for terminal Txn_Ref_88192. Node point localized to customer routing ledger tracking account number: ACC-7731920. Pattern flag: Structuring/High-frequency automated transfers detected."
}
```
### 2. Mid-Pipeline Data (Scout Agent Output)
The Scout Agent maps the behavior to local laws using RAG and outputs structured Pydantic objects:
```json
{
  "matched_typology": "Structuring / Smurfing",
  "confidence_score": 0.95,
  "justification": "The entity exhibits high-frequency automated transfers just below reporting thresholds, converging on a single ATM terminal node.",
  "supporting_nodes": ["N1", "N2", "N3"]
}
```

### 3. Final Artifact (Generated SAR & Audit Approval)
The pipeline returns a clean UI package via REST API, including the audited narrative and a graph-to-text linkage map for interactive frontend highlighting:

```json
{
  "audit_result": {
    "approved": true,
    "audit_score": 1.0,
    "critical_feedback": ""
  },
  "final_report_markdown": "Subject Overview: The account [1] belonging to Avdhoot Patil has been identified for potential money laundering activity...\n\nParagraph 2 Typology Match: The graph shows a suspicious account (N1) with an unusual large transaction to a merchant (N2)....",
  "ui_linkage_map": {
    "N1": "Paragraph 1, Paragraph 3",
    "N2": "Paragraph 2"
  }
}
```

---
## ⚙️ Prerequisites
To run this repository locally, you will need:

Python 3.9+

Neo4j Desktop (Running locally on port 7687)

Ollama (Installed locally with GPU acceleration recommended)

Required Models: Pull via terminal using ollama pull llama3 (and/or mistral)


```python
import foobar

# returns 'words'
foobar.pluralize('word')

# returns 'geese'
foobar.pluralize('goose')

# returns 'phenomenon'
foobar.singularize('phenomena')
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

