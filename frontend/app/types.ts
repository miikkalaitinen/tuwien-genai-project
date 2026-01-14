export interface GraphNodeMetadata {
  methodology: string;
  key_result: string;
  core_theory: string;
}

export interface GraphNodeData {
  label: string;
  metadata: GraphNodeMetadata;
  file_path: string;
}

export interface GraphEdgeData {
  relation_type: string;
  confidence: number;
  explanation: string;
}

export interface BackendNode {
  id: string;
  data: GraphNodeData;
}

export interface BackendEdge {
  id: string;
  source: string;
  target: string;
  data: GraphEdgeData;
}

export interface GraphResult {
  nodes: BackendNode[];
  edges: BackendEdge[];
}

export interface ProcessBatchResponse {
  status: string;
  progress: number;
  current_file: string;
  total_files: number;
  created_at: string;
  result: GraphResult | null;
}

export interface ProcessBatchStartResponse {
  job_id: string;
  status: string;
  message: string;
}
