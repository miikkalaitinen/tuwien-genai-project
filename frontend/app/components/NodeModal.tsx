import { Node } from "reactflow";

interface NodeModalProps {
  selectedNode: Node;
  closeModal: () => void;
}

export const NodeModal = ({ selectedNode, closeModal }: NodeModalProps) => {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-2xl p-8 max-w-xl w-full relative border border-gray-300">
        <button
          className="absolute top-3 right-3 text-gray-500 hover:text-gray-800 text-2xl font-bold"
          onClick={closeModal}
          aria-label="Close"
        >
          &times;
        </button>
        <div className="mb-6">
          <div className="text-2xl font-extrabold mb-4 text-gray-900">Paper Details</div>
          <div className="mb-3">
            <span className="font-semibold text-blue-700">Title:</span> <span className="text-gray-800">{selectedNode.data?.label || selectedNode.id}</span>
          </div>
          <div className="mb-3">
            <span className="font-semibold text-gray-900">Core Theory:</span>
            <div className="mt-2 px-3 py-2 rounded bg-gray-100 text-gray-900 whitespace-pre-line border border-gray-200">
              {selectedNode.data?.metadata?.core_theory}
            </div>
          </div>
          <div className="mb-3">
            <span className="font-semibold text-gray-900">Methodology:</span>
            <div className="mt-2 px-3 py-2 rounded bg-gray-100 text-gray-900 whitespace-pre-line border border-gray-200">
              {selectedNode.data?.metadata?.methodology}
            </div>
          </div>
          <div className="mb-3">
            <span className="font-semibold text-gray-900">Key Result:</span>
            <div className="mt-2 px-3 py-2 rounded bg-gray-100 text-gray-900 whitespace-pre-line border border-gray-200">
              {selectedNode.data?.metadata?.key_result}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
