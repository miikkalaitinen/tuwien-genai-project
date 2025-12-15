"use client";

import { useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge
} from 'reactflow';
import 'reactflow/dist/style.css';

const mocknodes = [
  { id: '1', position: { x: 250, y: 100 }, data: { label: 'Paper A: Transformers' } },
  { id: '2', position: { x: 100, y: 300 }, data: { label: 'Paper B: BERT' } },
  { id: '3', position: { x: 400, y: 300 }, data: { label: 'Paper C: GPT-3' } },
];

const mockedges = [
  { id: 'e1-2', source: '1', target: '2', label: 'extends' },
  { id: 'e1-3', source: '1', target: '3', label: 'contradicts' },
];

export default function GraphCanvas() {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [nodes, setNodes, onNodesChange] = useNodesState(mocknodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(mockedges);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  );

  return (
    <div className="w-full h-screen bg-gray-600">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}