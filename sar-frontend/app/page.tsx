'use client';

import { useState, useCallback } from 'react';
import axios from 'axios';
import ReactFlow, { 
  Background, 
  Controls, 
  Node, 
  Edge,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange
} from 'reactflow';
import 'reactflow/dist/style.css';
import ReactMarkdown from 'react-markdown';
import { ShieldAlert, Activity, FileText } from 'lucide-react';

export default function Dashboard() {
  // --- UI STATE ---
  const [loading, setLoading] = useState(false);
  const [activeParagraphs, setActiveParagraphs] = useState<string[]>([]);
  
  // --- DATA STATE ---
  const [reportText, setReportText] = useState<string>("Awaiting investigation payload...");
  const [linkageMap, setLinkageMap] = useState<Record<string, string>>({});
  const [auditResult, setAuditResult] = useState<any>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // React Flow Handlers
  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  // --- API CALL TO YOUR PYTHON BACKEND ---
  const runInvestigation = async () => {
    setLoading(true);
    try {
      // Mock alert payload - in a real app, this comes from an input field
      const payload = {
        alert_id: "ALRT-2026-99482",
        account_number: "8001002",
        risk_type: "Velocity Anomaly",
        timestamp: new Date().toISOString()
      };

      // Call your FastAPI server
      const response = await axios.post('http://127.0.0.1:8000/api/investigate', payload, {
        timeout: 300000 // Tell the browser to wait up to 5 minutes for the AI to finish thinking
      },);
      const data= response.data;
      setReportText(data.final_report_markdown);
      setLinkageMap(data.ui_linkage_map);
      setAuditResult(data.audit_result);

      // Transform backend Neo4j data into React Flow format
     // Smart Layout & Styling for Nodes
      const formattedNodes = data.graph_data.nodes.map((n: any, index: number) => {
        // Color code based on entity type
        let bgColor = '#1e293b'; // Default dark blue
        let borderColor = '#475569';
        
        if (n.labels.includes("Customer")) {
          bgColor = '#064e3b'; // Emerald dark
          borderColor = '#10b981';
        } else if (n.labels.includes("Merchant") || n.labels.includes("ATM")) {
          bgColor = '#7f1d1d'; // Red dark
          borderColor = '#ef4444';
        } else if (n.labels.includes("Account")) {
          bgColor = '#1e3a8a'; // Royal blue
          borderColor = '#3b82f6';
        }

        return {
          id: n.id,
          // Arrange them diagonally so they never overlap
          position: { x: 100 + (index * 250), y: 100 + (index * 150) }, 
          data: { label: `${n.labels[0]}\n${n.properties.name || n.id}` }, // Show the actual name on the node!
          style: { 
            background: bgColor, 
            color: 'white', 
            border: `2px solid ${borderColor}`, 
            borderRadius: '12px', 
            padding: '15px',
            fontWeight: 'bold',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)'
          }
        };
      });
      
      const formattedEdges = data.graph_data.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.type,
        animated: true,
        style: { stroke: '#3b82f6' }
      }));

      setNodes(formattedNodes);
      setEdges(formattedEdges);

    } catch (error) {
      console.error("Investigation failed:", error);
      setReportText("⚠️ Critical Error: Could not connect to Python backend.");
    }
    setLoading(false);
  };

  // --- THE MAGIC HOVER/CLICK LOGIC ---
  const handleNodeClick = (event: any, node: Node) => {
    // Look up the node ID in the linkage map we got from the backend
    const linkedParagraphsStr = linkageMap[node.id]; 
    if (linkedParagraphsStr) {
      // Example: "Paragraph 1, Paragraph 3" -> ["Paragraph 1", "Paragraph 3"]
      const paragraphs = linkedParagraphsStr.split(',').map(s => s.trim());
      setActiveParagraphs(paragraphs);
    } else {
      setActiveParagraphs([]);
    }
  };

  const handlePaneClick = () => {
    // Clear highlights when clicking empty space
    setActiveParagraphs([]);
  };

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200">
      
      {/* TOP NAVIGATION BAR */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900">
        <div className="flex items-center gap-3">
          <ShieldAlert className="text-blue-500 w-8 h-8" />
          <h1 className="text-xl font-bold tracking-wider">SAR AUTONOMOUS INTELLIGENCE UNIT</h1>
        </div>
        <button 
          onClick={runInvestigation}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-md font-semibold transition-all disabled:opacity-50"
        >
          {loading ? "Agents Investigating..." : "Launch Investigation"}
        </button>
      </header>

      {/* SPLIT WINDOW LAYOUT */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* LEFT PANEL: NETWORK GRAPH (50%) */}
        <div className="w-1/2 border-r border-slate-800 relative bg-slate-950">
          <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-slate-900/80 p-2 rounded-md border border-slate-700">
            <Activity className="text-emerald-400 w-5 h-5" />
            <span className="text-sm font-medium">Forensic Topology Map</span>
          </div>
          
          <ReactFlow 
            nodes={nodes} 
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            onPaneClick={handlePaneClick}
            fitView
            className="dark"
          >
            <Background color="#334155" gap={16} />
            <Controls className="bg-slate-800 fill-white" />
          </ReactFlow>
        </div>

        {/* RIGHT PANEL: GENERATED SAR REPORT (50%) */}
        <div className="w-1/2 overflow-y-auto p-8 bg-slate-900">
          <div className="flex items-center justify-between mb-8 border-b border-slate-800 pb-4">
            <div className="flex items-center gap-2">
              <FileText className="text-blue-400 w-6 h-6" />
              <h2 className="text-2xl font-bold text-white">Official SAR Narrative</h2>
            </div>
            
            {/* Auditor Badge */}
            {auditResult && (
              <span className={`px-3 py-1 rounded-full text-xs font-bold ${auditResult.approved ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/50' : 'bg-red-500/20 text-red-400 border border-red-500/50'}`}>
                {auditResult.approved ? '✅ Auditor Approved' : '⚠️ Audit Failed'}
              </span>
            )}
          </div>

          {/* Report Markdown Container */}
          <div className="prose prose-invert prose-blue max-w-none">
             <ReactMarkdown>{reportText}</ReactMarkdown>
          </div>
          
          {/* Debug Panel to show which paragraphs are currently active/highlighted */}
          {activeParagraphs.length > 0 && (
            <div className="mt-8 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg text-sm text-blue-300">
              <strong>Active Node Triggers:</strong> {activeParagraphs.join(', ')}
              <br/>
              <span className="text-xs text-slate-400 italic">
                (In the next step, we will use these active triggers to actually highlight the text above!)
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}