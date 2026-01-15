'use client'

import { useCallback, useEffect, useState } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  useNodesState,
  useEdgesState, 
  Edge,
  Node, 
  MarkerType
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ProcessBatchResponse } from '../types';
import CustomEdge from './CustomEdge';
import { EdgeModal } from './EdgeModal';
import { NodeModal } from './NodeModal';

interface GraphCanvasProps {
  nodes: Node[];
  edges: Edge[];
  loading: boolean;
  loadingProgress?: ProcessBatchResponse | null;
}

const RELATION_COLORS: Record<string, string> = {
  Supports: '#22c55e',
  Contradicts: '#ef4444',
  Extends: '#3b82f6',
  Default: '#94a3b8'
};

const edgeTypes = {
  custom: CustomEdge,
};

export default function GraphCanvas({ nodes: initialNodes, edges: initialEdges, loading, loadingProgress }: GraphCanvasProps) {
  
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [openModal, setOpenModal] = useState<Node | Edge | null>(null);


  // Function to check if modalOpen is type Edge
  const isEdge = (item: Node | Edge | null): item is Edge => {
    return item !== null && 'source' in item && 'target' in item;
  };

  // Function to check if modalOpen is type Node
  const isNode = (item: Node | Edge | null): item is Node => {
    return item !== null && 'position' in item;
  };

  useEffect(() => {
    const styledEdges: Edge[] = initialEdges.map((edge) => {
      const relationType = edge.data?.relation_type || 'Default';
      const color = RELATION_COLORS[relationType] || RELATION_COLORS.Default;

      return {
        ...edge,
        type: 'custom',
        animated: relationType === 'Extends',
        style: {
          stroke: color,
          strokeWidth: 2,
          strokeDasharray: '0',
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: color,
        },
        label: relationType !== 'Default' ? relationType : '',
        data: { ...edge.data },
      };
    });

    setNodes(initialNodes);
    setEdges(styledEdges);
  }, [initialNodes, initialEdges]);

  const handleEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    event.stopPropagation();
    setOpenModal(edge);
  }, []);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    event.stopPropagation();
    setOpenModal(node);
  }, []);

  return (
    <div className="w-full h-screen bg-gray-600 relative">
      {loading && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 text-white">
          <div className="flex flex-col items-center p-6 bg-gray-800 rounded-lg shadow-xl border border-gray-700 max-w-md w-full">
            {loadingProgress ? (
              <>
                <div className="text-xl font-bold mb-4">Analyzing Papers...</div>
                
                <div className="w-full bg-gray-700 rounded-full h-4 mb-2">
                  <div 
                    className="bg-blue-600 h-4 rounded-full transition-all duration-500 ease-out" 
                    style={{ width: `${loadingProgress.progress}%` }}
                  ></div>
                </div>
                
                <div className="flex justify-between w-full text-sm text-gray-300 mb-2">
                  <span>{loadingProgress.progress}%</span>
                  <span>{loadingProgress.status}</span>
                </div>

                <div className="text-sm text-gray-400 truncate w-full text-center">
                  Current file: <span className="text-blue-400">{loadingProgress.current_file}</span>
                </div>
                
                {loadingProgress.total_files > 0 && (
                   <div className="text-xs text-gray-500 mt-2">
                     Processing {loadingProgress.total_files} files
                   </div>
                )}
              </>
            ) : (
              <div className="text-xl font-bold animate-pulse">Initializing...</div>
            )}
          </div>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onEdgeClick={handleEdgeClick}
        onNodeClick={handleNodeClick}
        fitView
        edgeTypes={edgeTypes}
      >
        <Background />
        <Controls />
      </ReactFlow>

      {openModal && isEdge(openModal) && openModal && (
        <EdgeModal
          selectedEdge={openModal} 
          nodes={nodes} 
          closeModal={() => setOpenModal(null)} 
        />
      )}

      {openModal && isNode(openModal) && (
        <NodeModal
          selectedNode={openModal} 
          closeModal={() => setOpenModal(null)} 
        />
      )}
    </div>
  );
}