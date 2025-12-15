import GraphCanvas from "./components/GraphCanvas";
import Sidebar from "./components/Sidebar";

export default function Home() {
  return (
    <main className="flex h-screen w-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 relative">
        <GraphCanvas />
      </div>
    </main>
  );
}