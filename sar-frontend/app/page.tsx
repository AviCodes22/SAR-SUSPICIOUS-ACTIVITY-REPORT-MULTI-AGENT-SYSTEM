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
  // UI STATE
  const [loading, setLoading] = useState(false);
  const [activeParagraphs, setActiveParagraphs] = useState<string[]>([]);
  
  // DATA STATE
  const [reportText, setReportText] = useState<string>("Awaiting investigation payload...");
  const [linkageMap, setLinkageMap] = useState<Record<string, string>>({});
  const [auditResult, setAuditResult] = useState<any>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // REACT FLOW HANDLERS
  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  // API INVESTIGATION HANDLER
  const runInvestigation = async () => {
    setLoading(true);
    try {
      const payload = {
        alert_id: "ALRT-IBM-001",
        account_number: "100428660",
        risk_type: "High-Value Laundering Transfer",
        timestamp: new Date().toISOString()
      };

      const response = await axios.post('http://127.0.0.1:8000/api/investigate', payload, {
        timeout: 600000 
      });
      
      const data = response.data;
      setReportText(data.final_report_markdown);
      setLinkageMap(data.ui_linkage_map);
      setAuditResult(data.audit_result);

      // NODE FORMATTING
      const formattedNodes = data.graph_data.nodes.map((n: any, index: number) => {
        let bgColor = '#1e293b'; 
        let borderColor = '#475569';
        
        if (n.labels.includes("Customer")) {
          bgColor = '#064e3b'; 
          borderColor = '#10b981';
        } else if (n.labels.includes("Merchant") || n.labels.includes("ATM")) {
          bgColor = '#7f1d1d'; 
          borderColor = '#ef4444';
        } else if (n.labels.includes("Account")) {
          bgColor = '#1e3a8a'; 
          borderColor = '#3b82f6';
        }

        return {
          id: n.id,
          position: { x: 100 + (index * 250), y: 100 + (index * 150) }, 
          data: { label: `${n.labels[0]}\n${n.properties.name || n.id}` }, 
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
      
      // EDGE FORMATTING
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

  // NODE CLICK HANDLER
  const handleNodeClick = (event: any, node: Node) => {
    const linkedParagraphsStr = linkageMap[node.id]; 
    if (linkedParagraphsStr) {
      const paragraphs = linkedParagraphsStr.split(',').map(s => s.trim());
      setActiveParagraphs(paragraphs);
    } else {
      setActiveParagraphs([]);
    }
  };

  // PANE CLICK HANDLER
  const handlePaneClick = () => {
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
        
        {/* LEFT PANEL */}
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

        {/* RIGHT PANEL */}
        <div className="w-1/2 overflow-y-auto p-10 bg-gray-100 flex flex-col items-center">
          
          {/* A4 PAPER CONTAINER */}
          <div className="bg-white text-black w-full max-w-3xl shadow-xl border border-gray-300 p-10 rounded-sm">
            
            {/* HEADER */}
            <div className="flex items-center justify-between mb-6 border-b-2 border-black pb-4">
              <div className="flex flex-col">
                <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">FIU-IND</h1>
                <h2 className="text-sm font-bold text-gray-600 uppercase tracking-widest">Financial Intelligence Unit - India</h2>
                <h3 className="text-lg font-semibold mt-2">SUSPICIOUS TRANSACTION REPORT (STR)</h3>
              </div>
              
              {/* AUDITOR BADGE */}
              {auditResult && (
                <div className={`px-4 py-2 text-sm font-bold border-2 ${auditResult.approved ? 'border-green-600 text-green-700 bg-green-50' : 'border-red-600 text-red-700 bg-red-50'}`}>
                  {auditResult.approved ? 'APPROVED FOR FILING' : 'AUDIT REJECTED'}
                </div>
              )}
            </div>

            {/* MARKDOWN CONTAINER */}
            <div className="prose prose-sm max-w-none text-black prose-headings:text-black prose-headings:border-b prose-headings:border-gray-200 prose-headings:pb-1 prose-strong:text-black">
               <ReactMarkdown>{reportText}</ReactMarkdown>
            </div>
          </div>
          
          {/* DEBUG PANEL */}
          {activeParagraphs.length > 0 && (
            <div className="mt-8 p-4 bg-blue-900/20 border border-blue-500/30 rounded-lg text-sm text-blue-300 w-full max-w-3xl">
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