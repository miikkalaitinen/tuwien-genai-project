'use client'

import { useState } from "react";
import GraphCanvas from "./components/GraphCanvas";
import Sidebar from "./components/Sidebar";
import ErrorBanner from "./components/ErrorBanner";
import { Edge, Node } from "reactflow";
import { ProcessBatchResponse } from "./types";


export default function Home() {
  const [graphData, setGraphData] = useState<{ nodes: Node[] | [], edges: Edge[] | [] }>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingProgress, setLoadingProgress] = useState<ProcessBatchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleError = (msg: string) => {
    setError(msg);
  };

  return (
    <main className="flex h-screen w-screen overflow-hidden relative">
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}
      <Sidebar 
        onGraphUpdate={setGraphData} 
        setLoading={setLoading} 
        onProgressUpdate={setLoadingProgress} 
        loading={loading}
        onError={handleError}
      />  
      
      <div className="flex-1 relative">
        <GraphCanvas 
          nodes={graphData.nodes} 
          edges={graphData.edges} 
          loading={loading}
          loadingProgress={loadingProgress}
        />
      </div>
    </main>
  );
}