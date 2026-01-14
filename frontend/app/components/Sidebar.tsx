"use client";

import React, { useState } from 'react';
import { Upload, BookOpen, Microscope, FileText, Trash, Scale, List } from 'lucide-react';
import { Node, Edge } from "reactflow";
import { ProcessBatchResponse, ProcessBatchStartResponse } from '../types';

interface SidebarProps {
  onGraphUpdate: (data: { nodes: Node[], edges: Edge[] }) => void;
  setLoading: (loading: boolean) => void;
  onProgressUpdate: (progress: ProcessBatchResponse | null) => void;
  loading: boolean;
}
  
export default function Sidebar({ onGraphUpdate, setLoading, onProgressUpdate, loading }: SidebarProps) {
    
  const [user, setUser] = useState<'student' | 'researcher'>('student');
  const [mode, setMode] = useState<'summarise' | 'critique'>('summarise');
  const [files, setFiles] = useState<File[]>([]);

  const handleSelectFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  }

  const fetchResults = async (formData: FormData) => {
    const response = await fetch("http://localhost:8000/graph", {
      method: "POST",
      body: formData,
    });
    return response.json();
  };

  const handleGenerateGraph = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append("files", file); 
    });
    
    formData.append("mode", mode);
    formData.append("user_type", user);

    try {
      const startResponse = await fetch("http://localhost:8000/process-batch", {
        method: "POST",
        body: formData,
      });
      
      const startData: ProcessBatchStartResponse = await startResponse.json();
      const jobId = startData.job_id;

      let processing = true;
      while (processing) {
        const statusResponse = await fetch(`http://localhost:8000/batch-status/${jobId}`);
        const statusData: ProcessBatchResponse = await statusResponse.json();
        
        onProgressUpdate(statusData);

        if (statusData.status === 'completed' && statusData.result) {
          const nodesWithPos = statusData.result.nodes.map((node, index) => ({
            ...node,
            position: { x: 100 * (index % 5), y: 100 * Math.floor(index / 5) }
          }));

          onGraphUpdate({
            nodes: nodesWithPos, 
            edges: statusData.result.edges 
          });
          processing = false;
        } else if (statusData.status === 'failed') {
          console.error("Job failed:", statusData);
          processing = false;
        } else {
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      }
      
    } catch (error) {
      console.error("Upload failed:", error);
    } finally {
      setLoading(false);
      onProgressUpdate(null);
    }
  };

  return (
    <div className="w-80 h-screen bg-gray-800 flex flex-col p-4  z-10">
      <h1 className="text-xl font-bold mb-6 text-gray-400">Research Navigator</h1>
      <div className="mb-8">
        <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 block">
          User Type
        </label>
        <div className="flex bg-gray-600 p-1 rounded-lg">
          <button
            onClick={() => setUser('student')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              user === 'student' ? 'bg-gray-800 text-green-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            Student
          </button>
          <button
            onClick={() => setUser('researcher')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              user === 'researcher' ? 'bg-gray-800  text-purple-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <Microscope className="w-4 h-4 mr-2" />
            Researcher
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 italic">
          {user === 'student' && 'Focus on clear explanations and foundational concepts.'}
          {user === 'researcher' && 'Emphasize advanced analysis and technical depth.'}
        </p>
      </div>
      <div className="mb-8">
        <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 block">
          Mode
        </label>
        <div className="flex bg-gray-600 p-1 rounded-lg">
          <button
            onClick={() => setMode('summarise')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'summarise' ? 'bg-gray-800 text-blue-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <List className="w-4 h-4 mr-2" />
            Summarise
          </button>
          <button
            onClick={() => setMode('critique')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'critique' ? 'bg-gray-800 text-red-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <Scale className="w-4 h-4 mr-2" />
            Critique
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 italic">
          { mode === 'summarise' && "Provides concise summaries of key points." }
          { mode === 'critique' && "Analyzes strengths and weaknesses." }
        </p>
      </div>
      <div className="mb-6">
        <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 block">
          Documents
        </label>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:bg-gray-500 transition-colors text-center cursor-pointer relative">
          <input 
            type="file" 
            multiple 
            accept=".pdf"
            onChange={handleSelectFiles}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <span className="text-sm text-gray-300 block">Drag PDFs here</span>
          <span className="text-xs text-gray-400 block mt-1">or click to browse</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {files.length > 0 && (
          <div className="space-y-2">
            {files.map((file, i) => (
              <div key={i} className="flex items-center p-2 bg-gray-300 rounded border border-gray-500">
                <FileText className="w-4 h-4 text-gray-400 mr-3" />
                <span className="text-sm text-gray-700 truncate">{file.name}</span>
                <button className="ml-auto">
                  <Trash 
                    className="w-4 h-4 text-red-500 ml-auto hover:text-red-700" 
                    onClick={() => setFiles(files.filter((_, index) => index !== i))} 
                  />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
      <button 
        className="w-full bg-gray-700 cursor-pointer text-white py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        disabled={files.length === 0}
        onClick={handleGenerateGraph}
      >
        {loading ? "Analyzing..." : "Generate Graph"}
      </button>
    </div>
  );
}