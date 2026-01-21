import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGlobalState } from '@/hooks/useGlobalState';
import Navbar from "@/components/Navbar";
import LiveDataDashboard from "@/components/LiveDataDashboard";

const WarRoom = () => {
  const navigate = useNavigate();
  const { isInitialized, isAuthenticated } = useGlobalState();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      navigate('/auth');
    }
  }, [isInitialized, isAuthenticated, navigate]);

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-16">
        <LiveDataDashboard />
      </main>
    </div>
  );
};

export default WarRoom;
