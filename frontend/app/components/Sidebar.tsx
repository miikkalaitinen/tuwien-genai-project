"use client";

import React, { useState } from 'react';
import { Upload, BookOpen, Microscope, FileText, TrashIcon } from 'lucide-react';

export default function Sidebar() {
  const [mode, setMode] = useState<'student' | 'researcher'>('student');
  const [files, setFiles] = useState<File[]>([]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  return (
    <div className="w-80 h-screen bg-gray-800 flex flex-col p-4  z-10">
      <h1 className="text-xl font-bold mb-6 text-gray-400">Research Navigator</h1>
      <div className="mb-8">
        <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider mb-3 block">
          Perspective Mode
        </label>
        <div className="flex bg-gray-600 p-1 rounded-lg">
          <button
            onClick={() => setMode('student')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'student' ? 'bg-gray-800 text-green-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <BookOpen className="w-4 h-4 mr-2" />
            Student
          </button>
          <button
            onClick={() => setMode('researcher')}
            className={`flex-1 flex items-center cursor-pointer justify-center py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'researcher' ? 'bg-gray-800  text-purple-500' : 'text-gray-300 hover:text-gray-100 hover:bg-gray-500'
            }`}
          >
            <Microscope className="w-4 h-4 mr-2" />
            Researcher
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 italic">
          {mode === 'student' 
            ? "Highlights definitions & basic concepts." 
            : "Highlights contradictions & methodology."}
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
            onChange={handleFileUpload}
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
                  <TrashIcon 
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
      >
        Generate Graph
      </button>
    </div>
  );
}