import Navbar from "@/components/Navbar";
import WarRoomDashboard from "@/components/WarRoomDashboard";

const WarRoom = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-16">
        <WarRoomDashboard />
      </main>
    </div>
  );
};

export default WarRoom;
