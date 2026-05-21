'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useReactToPrint } from 'react-to-print';
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
} 


from 'reactflow';
import 'reactflow/dist/style.css';
import { ShieldAlert, Activity, FileText, Download } from 'lucide-react';

export default function Dashboard() {
  // UI STATE
  const [loading, setLoading] = useState(false);
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);
  
  // DATA STATE
  const [reportData, setReportData] = useState<any>(null);
  const [auditResult, setAuditResult] = useState<any>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // REACT FLOW HANDLERS
  const onNodesChange = useCallback((changes: NodeChange[]) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: EdgeChange[]) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);

  // PDF EXPORT HOOK
  const reportRef = useRef<HTMLDivElement>(null);
  const handlePrint = useReactToPrint({
    contentRef: reportRef,
    documentTitle: `FIU_IND_STR_${new Date().toISOString().split('T')[0]}`,
  });

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
      
      // Parse the new JSON string coming from the Drafter
      try {
        const parsedReport = JSON.parse(data.final_report_markdown);
        setReportData(parsedReport);
      } catch (e) {
        console.error("Failed to parse report JSON", e);
      }
      
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
          id: String(n.id), // Ensure ID is a string for hover matching
          position: { x: 100 + (index * 250), y: 100 + (index * 150) }, 
          data: { 
            label: `${n.labels[0]}\n${n.properties.name || n.id}`,
            originalBg: bgColor,
            originalBorder: borderColor
          }, 
          style: { 
            background: bgColor, 
            color: 'white', 
            border: `2px solid ${borderColor}`, 
            borderRadius: '12px', 
            padding: '15px',
            fontWeight: 'bold',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
            transition: 'all 0.3s ease'
          }
        };
      });
      
      // EDGE FORMATTING
      const formattedEdges = data.graph_data.edges.map((e: any) => ({
        id: e.id,
        source: String(e.source),
        target: String(e.target),
        label: e.type,
        animated: true,
        style: { stroke: '#3b82f6' }
      }));

      setNodes(formattedNodes);
      setEdges(formattedEdges);

    } catch (error) {
      console.error("Investigation failed:", error);
    }
    setLoading(false);
  };

  // HOVER EFFECT HOOK
  // Dynamically dims non-hovered nodes and glows the hovered node
  useEffect(() => {
    setNodes((currentNodes) => 
      currentNodes.map((node) => {
        const isHovered = hoveredNodeId === node.id;
        const isDimmed = hoveredNodeId !== null && !isHovered;
        
        return {
          ...node,
          style: {
            ...node.style,
            opacity: isDimmed ? 0.3 : 1,
            boxShadow: isHovered ? '0 0 20px #3b82f6' : '0 4px 6px -1px rgba(0, 0, 0, 0.5)',
            border: `2px solid ${isHovered ? '#60a5fa' : node.data.originalBorder}`,
            transform: isHovered ? 'scale(1.05)' : 'scale(1)'
          }
        };
      })
    );
  }, [hoveredNodeId]);

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-200">
      
      {/* TOP NAVIGATION BAR */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900">
        <div className="flex items-center gap-3">
          <ShieldAlert className="text-blue-500 w-8 h-8" />
          <h1 className="text-xl font-bold tracking-wider">SAR AUTONOMOUS INTELLIGENCE UNIT</h1>
        </div>
        
        <div className="flex gap-4">
          {/* PDF EXPORT BUTTON */}
          <button 
            onClick={() => handlePrint()}
            disabled={!reportData}
            className="flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-md font-semibold transition-all disabled:opacity-50"
          >
            <Download className="w-4 h-4" /> Export PDF
          </button>

          <button 
            onClick={runInvestigation}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-md font-semibold transition-all disabled:opacity-50"
          >
            {loading ? "Agents Investigating..." : "Launch Investigation"}
          </button>
        </div>
      </header>

      {/* SPLIT WINDOW LAYOUT */}
      <div className="flex flex-1 overflow-hidden">
        
        {/* LEFT PANEL: GRAPH */}
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
            fitView
            className="dark"
          >
            <Background color="#334155" gap={16} />
            <Controls className="bg-slate-800 fill-white" />
          </ReactFlow>
        </div>

        {/* RIGHT PANEL: DARK FIU-IND REPORT WITH PRINT TARGET */}
        <div className="w-1/2 overflow-y-auto p-8 bg-slate-950 flex flex-col items-center">
          
          {reportData ? (
            <div 
              ref={reportRef} 
              className="bg-slate-950 text-slate-300 p-8 rounded-xl shadow-2xl border border-slate-800 w-full max-w-3xl font-sans relative 
                         print:bg-white print:text-black print:shadow-none print:border-none print:p-10"
            >
              
              {/* Official Header */}
              <div className="border-b-2 border-blue-900 print:border-black pb-6 mb-8 flex justify-between items-start">
                <div>
                  <h1 className="text-4xl font-black text-blue-500 print:text-black tracking-wider">FIU-IND</h1>
                  <h2 className="text-xs font-semibold tracking-widest text-slate-400 print:text-gray-600 mt-1 uppercase">Financial Intelligence Unit - India</h2>
                  <h3 className="text-lg font-bold text-slate-100 print:text-black mt-4">SUSPICIOUS TRANSACTION REPORT (STR)</h3>
                </div>
                
                {/* Dynamic Badge - Hidden during print for a cleaner official look */}
                {auditResult && (
                  <div className={`px-4 py-2 border font-bold rounded text-sm print:hidden ${auditResult.approved ? 'bg-blue-900/30 border-blue-500 text-blue-400' : 'bg-red-900/30 border-red-500 text-red-400'}`}>
                    {auditResult.approved ? 'APPROVED FOR FILING' : 'AUDIT REJECTED'}
                  </div>
                )}
              </div>

              {/* PART 1 & 2 & 3: Details */}
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div className="bg-slate-900 print:bg-transparent p-4 rounded border border-slate-800 print:border-gray-300">
                  <h4 className="text-blue-400 print:text-black text-sm font-bold mb-3 border-b border-slate-800 print:border-gray-300 pb-2">PART 1: DETAILS OF REPORT</h4>
                  <p className="text-sm mb-1"><span className="text-slate-500 print:text-gray-600">Date of sending:</span> {reportData.part_1_date}</p>
                  <p className="text-sm"><span className="text-slate-500 print:text-gray-600">Replacement Report?:</span> {reportData.part_1_replacement || 'No'}</p>
                </div>
                
                <div className="bg-slate-900 print:bg-transparent p-4 rounded border border-slate-800 print:border-gray-300">
                  <h4 className="text-blue-400 print:text-black text-sm font-bold mb-3 border-b border-slate-800 print:border-gray-300 pb-2">PART 2 & 3: INSTITUTION</h4>
                  <p className="text-sm mb-1"><span className="text-slate-500 print:text-gray-600">Name of Bank:</span> {reportData.part_2_bank}</p>
                  <p className="text-sm"><span className="text-slate-500 print:text-gray-600">Branch:</span> {reportData.part_3_branch}</p>
                </div>
              </div>

              {/* PART 4 & 5: Individuals & Entities */}
              <div className="bg-slate-900 print:bg-transparent p-4 rounded border border-slate-800 print:border-gray-300 mb-6">
                <h4 className="text-blue-400 print:text-black text-sm font-bold mb-3 border-b border-slate-800 print:border-gray-300 pb-2">PART 4 & 5: LINKED INDIVIDUALS / ENTITIES</h4>
                <ul className="text-sm space-y-1">
                  {reportData.part_4_individuals?.map((person: string, idx: number) => (
                    <li key={idx} className="text-slate-300 print:text-black">• {person}</li>
                  ))}
                  {reportData.part_5_entities?.map((entity: string, idx: number) => (
                    <li key={idx} className="text-slate-300 print:text-black">• {entity}</li>
                  ))}
                </ul>
              </div>

              {/* PART 6: ACCOUNTS (INTERACTIVE HOVER STRIP) */}
              <div className="bg-slate-900 print:bg-transparent p-4 rounded border border-slate-800 print:border-gray-300 mb-6 relative overflow-hidden">
                <div className="absolute top-0 right-0 bg-blue-600 text-white text-[10px] px-2 py-1 font-bold rounded-bl-lg print:hidden">INTERACTIVE</div>
                <h4 className="text-blue-400 print:text-black text-sm font-bold mb-4 border-b border-slate-800 print:border-gray-300 pb-2">PART 6: LIST OF ACCOUNTS <span className="text-slate-500 text-xs font-normal print:hidden">(Hover to locate)</span></h4>
                <div className="flex flex-wrap gap-2">
                  {reportData.part_6_accounts?.map((accountId: string) => (
                    <span 
                      key={accountId}
                      onMouseEnter={() => setHoveredNodeId(String(accountId))}
                      onMouseLeave={() => setHoveredNodeId(null)}
                      className="font-mono text-xs bg-slate-950 print:bg-transparent border border-slate-700 print:border-none px-3 py-1.5 print:p-0 rounded cursor-pointer transition-all duration-200 hover:bg-blue-600 hover:border-blue-400 hover:text-white hover:scale-105 print:after:content-[',_'] last:print:after:content-['']"
                    >
                      {accountId}
                    </span>
                  ))}
                </div>
              </div>

              {/* PART 7: SUSPICIOUS TRANSACTION DETAILS */}
              <div className="bg-slate-900 print:bg-transparent p-5 rounded border border-slate-800 print:border-gray-300 mb-6">
                  <h4 className="text-blue-400 print:text-black text-sm font-bold mb-4 border-b border-slate-800 print:border-gray-300 pb-2">PART 7: DETAILS OF SUSPICIOUS TRANSACTION</h4>
                  <p className="text-sm mb-3"><span className="text-slate-500 print:text-gray-800 font-bold">7.1 Reason for suspicion:</span> {reportData.part_7_reason}</p>
                  <p className="text-sm leading-relaxed text-slate-300 print:text-black">
                    <span className="text-slate-500 print:text-gray-800 font-bold block mb-1">7.2 Grounds of Suspicion:</span>
                    {reportData.part_7_grounds}
                  </p>
              </div>

              {/* PART 8: ACTION TAKEN */}
              <div className="bg-slate-900 print:bg-transparent p-4 rounded border border-slate-800 print:border-gray-300">
                  <h4 className="text-blue-400 print:text-black text-sm font-bold mb-2 border-b border-slate-800 print:border-gray-300 pb-2">PART 8: DETAILS OF ACTION TAKEN</h4>
                  <p className="text-sm text-slate-300 print:text-black">{reportData.part_8_action}</p>
              </div>

            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-slate-600 border-2 border-dashed border-slate-800 rounded-xl w-full max-w-3xl">
               <FileText className="w-12 h-12 mb-4 opacity-50" />
               <p>Awaiting investigation payload...</p>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}