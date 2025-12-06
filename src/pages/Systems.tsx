import Navbar from "@/components/Navbar";
import SystemRegistryPanel from "@/components/SystemRegistryPanel";

const Systems = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🧠</span>
            <h1 className="text-3xl font-bold text-foreground">System Registry</h1>
          </div>
          
          <SystemRegistryPanel />
        </div>
      </main>
    </div>
  );
};

export default Systems;
