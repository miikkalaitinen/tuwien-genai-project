"use client";

import React, { useState } from 'react';
import { Upload, BookOpen, Microscope, FileText, Trash } from 'lucide-react';
import { Node, Edge } from "reactflow";
import { ProcessBatchResponse, ProcessBatchStartResponse } from '../types';

interface SidebarProps {
  onGraphUpdate: (data: { nodes: Node[], edges: Edge[] }) => void;
  setLoading: (loading: boolean) => void;
  onProgressUpdate: (progress: ProcessBatchResponse | null) => void;
  loading: boolean;
  onError: (msg: string) => void;
}
  
export default function Sidebar({ onGraphUpdate, setLoading, onProgressUpdate, loading, onError }: SidebarProps) {
    
  const [user, setUser] = useState<'student' | 'researcher'>('student');
  const [lastGeneration, setLastGeneration] = useState<{ user: 'student' | 'researcher', files: File[] } | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [papers, setPapers] = useState<{id: string, name: string}[]>([]);

  const handleSelectFiles = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files);
      setFiles(prevFiles => {
        const existingNames = new Set(prevFiles.map(f => f.name));
        const uniqueNewFiles = newFiles.filter(f => !existingNames.has(f.name));
        return [...prevFiles, ...uniqueNewFiles];
      });
    }
  }

  const handleUpdateGraph = async () => {
    if (papers.length === 0 || loading) return;
    
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/graph", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mode: user,
          papers: papers
        }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to start graph update (${response.status})`);
      }

      const startData: ProcessBatchStartResponse = await response.json();
      const jobId = startData.job_id;

      let processing = true;
      while (processing) {
        const statusResponse = await fetch(`http://localhost:8000/batch-status/${jobId}`);
        
        if (!statusResponse.ok) {
          throw new Error("Failed to check job status");
        }

        const statusData: ProcessBatchResponse = await statusResponse.json();
        
        onProgressUpdate(statusData);

        if (statusData.status === 'completed' && statusData.result) {
          const nodesWithPos = statusData.result.nodes.map((node, index) => ({
            ...node,
            position: { x: 100 * (index % 5), y: 100 * Math.floor(index / 5) }
          }));

          setPapers(statusData.result.nodes.map(n => ({
            id: n.id,
            name: n.data.label
          })));
          setLastGeneration({ user, files });

          onGraphUpdate({
            nodes: nodesWithPos, 
            edges: statusData.result.edges 
          });
          processing = false;
        } else if (statusData.status === 'failed') {
          console.error("Graph update failed:", statusData);
          onError(statusData.error || "Graph update failed with unknown error");
          processing = false;
        } else {
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }
    } catch (error) {
      console.error("Graph update failed:", error);
      onError(error instanceof Error ? error.message : "Failed to update graph");
    } finally {
      setLoading(false);
      onProgressUpdate(null);
    }
  };

  const hasDifferentFilesThanLastGeneration = () => {
    if (!lastGeneration) return false;
    if (files.length !== lastGeneration.files.length) return true;
    const lastFileNames = new Set(lastGeneration.files.map(f => f.name));
    return files.some(f => !lastFileNames.has(f.name));
  }
  
  const handleGenerateGraph = async () => {
    if (files.length === 0) return;
    
    setLoading(true);
    const formData = new FormData();
    
    files.forEach((file) => {
      formData.append("files", file); 
    });
    
    formData.append("user_type", user);

    try {
      const startResponse = await fetch("http://localhost:8000/process-batch", {
        method: "POST",
        body: formData,
      });

      if (!startResponse.ok) {
        throw new Error(`Failed to start processing (${startResponse.status})`);
      }
      
      const startData: ProcessBatchStartResponse = await startResponse.json();
      const jobId = startData.job_id;

      let processing = true;
      while (processing) {
        const statusResponse = await fetch(`http://localhost:8000/batch-status/${jobId}`);
        
        if (!statusResponse.ok) {
          throw new Error("Failed to check job status");
        }

        const statusData: ProcessBatchResponse = await statusResponse.json();
        
        onProgressUpdate(statusData);

        if (statusData.status === 'completed' && statusData.result) {
          const nodesWithPos = statusData.result.nodes.map((node, index) => ({
            ...node,
            position: { x: 100 * (index % 5), y: 100 * Math.floor(index / 5) }
          }));

          setPapers(statusData.result.nodes.map(n => ({
            id: n.id,
            name: n.data.label
          })));
          setLastGeneration({ user, files });

          onGraphUpdate({
            nodes: nodesWithPos, 
            edges: statusData.result.edges 
          });
          processing = false;
        } else if (statusData.status === 'failed') {
          console.error("Job failed:", statusData);
          onError(statusData.error || "Processing failed with unknown error");
          processing = false;
        } else {
          await new Promise(resolve => setTimeout(resolve, 5000));
        }
      }
      
    } catch (error) {
      console.error("Upload failed:", error);
      onError(error instanceof Error ? error.message : "Upload failed");
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
          Perspective
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
      <div className="mb-4">
        <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 block">
          How it works
        </label>
        <p className="text-xs text-gray-400 leading-relaxed italic">
          Upload your PDFs to begin; the AI then parses semantic findings and maps 
          relationships based on your chosen user perspective.
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
        className={`w-full mt-4 cursor-pointer text-white py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          (files.length > 0 && (papers.length > 0 && (user !== lastGeneration?.user || hasDifferentFilesThanLastGeneration())))
            ? 'bg-blue-600 hover:bg-blue-700 animate-pulse' 
            : 'bg-gray-700 hover:bg-gray-800'
        }`}
        disabled={files.length === 0 && (papers.length === 0 || user === lastGeneration?.user && !hasDifferentFilesThanLastGeneration()) || loading}
        onClick={() => {
          if (files.length > 0) {
            handleGenerateGraph();
          } else {
            handleUpdateGraph();
          }
        }}
      >
        {loading ? (
             "Analyzing..." 
        ) : (
          hasDifferentFilesThanLastGeneration() ? "Regenerate with new papers" :
          papers.length > 0 && user !== lastGeneration?.user ? "Regenerate with new perspective" :
          "Generate Graph"
        )}
      </button>
    </div>
  );
}