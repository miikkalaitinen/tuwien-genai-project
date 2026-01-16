import { Edge, Node } from "reactflow";

interface EdgeModalProps {
  selectedEdge: Edge;
  nodes: Node[];
  closeModal: () => void;
}

export const EdgeModal = ({ selectedEdge, nodes, closeModal }: EdgeModalProps) => {
return (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
    <div className="bg-white rounded-xl shadow-2xl max-w-xl w-full relative border border-gray-300 max-h-[85vh] flex flex-col">
      <button
        className="absolute top-3 right-3 text-gray-500 hover:text-gray-800 text-2xl font-bold z-10"
        onClick={closeModal}
        aria-label="Close"
      >
        &times;
      </button>
      <div className="p-8 overflow-y-auto">
        <div className="mb-6">
          <div className="text-2xl font-extrabold mb-4 text-gray-900">Connection Details</div>
          <div className="mb-4 flex flex-col gap-2">
            <div>
              <span className="font-semibold text-blue-700">Paper A (Target):</span> <span className="text-gray-800">{nodes.find(n => n.id === selectedEdge.source)?.data?.label || selectedEdge.source}</span>
            </div>
            <div>
              <span className="font-semibold text-green-700">Paper B (Origin):</span> <span className="text-gray-800">{nodes.find(n => n.id === selectedEdge.target)?.data?.label || selectedEdge.target}</span>
            </div>
          </div>
          <div className="mb-3">
            <span className="font-semibold text-gray-800">Type:</span> <span className="text-gray-800">{selectedEdge.data?.relation_type}</span>
          </div>
          <div className="mb-3">
            <span className="font-semibold text-gray-800">Confidence:</span> <span className="text-gray-800">{selectedEdge.data?.confidence}</span>
          </div>
          <div className="mb-3 mt-2 px-3 py-2 rounded bg-gray-100 text-gray-900 whitespace-pre-line border border-gray-200">
            <span className="font-semibold text-gray-800">Explanation:</span>
            <div className="mt-1 text-gray-700">
              {selectedEdge.data?.explanation}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)
}