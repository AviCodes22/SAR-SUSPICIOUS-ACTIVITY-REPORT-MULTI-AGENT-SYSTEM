from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


from pipeline import system_pipeline

app = FastAPI(
    title="SAR Multi-Agent Intelligence API",
    description="Backend endpoint for autonomous financial compliance investigations.",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows your Streamlit/React frontend to talk to this server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AlertPayload(BaseModel):
    alert_id: str
    account_number: str
    risk_type: str
    timestamp: str

#Create the main POST endpoint
@app.post("/api/investigate")
def trigger_investigation(alert: AlertPayload):
    print(f"🚀 Incoming Alert Received from UI: {alert.alert_id} for Account {alert.account_number}")
    
    # Map the incoming API data to your LangGraph state structure
    initial_state_payload = {
        "messages": [],
        "raw_alert": {
            "alert_id": alert.alert_id,
            "account_number": alert.account_number,
            "risk_type": alert.risk_type,
            "timestamp": alert.timestamp
        },
        "alert_details": {},
        "generated_query": "",
        "graph_visualization": {},
        "typology_reasoning": {},
        "str_form_data": {},
        "narrative_draft": "",
        "forensic_linkages": {},
        "audit_review": {}
    }

    try:
        # Fire the autonomous agents!
        pipeline_results = system_pipeline.invoke(initial_state_payload)
        
        # Return the critical UI components back to the frontend
        return {
            "status": "success",
            "graph_data": pipeline_results.get("graph_visualization", {}),
            "typology_scan": pipeline_results.get("typology_reasoning", {}),
            "audit_result": pipeline_results.get("audit_review", {}),
            "final_report_markdown": pipeline_results.get("narrative_draft", ""),
            "ui_linkage_map": pipeline_results.get("forensic_linkages", {})
        }
    except Exception as e:
        print(f"❌ API Execution Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Runs the server locally on port 8000
    print("Starting SAR Backend API Server on http://localhost:8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)