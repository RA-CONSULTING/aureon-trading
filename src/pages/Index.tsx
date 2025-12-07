import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGlobalState } from '@/hooks/useGlobalState';
import AureonDashboard from '@/components/AureonDashboard';

// Uses global state - no more redundant auth checks here
// GlobalSystemsManager handles all auth and initialization

export default function Index() {
  const navigate = useNavigate();
  const { isInitialized, isAuthenticated } = useGlobalState();

  useEffect(() => {
    // Redirect to auth if initialized but not authenticated
    if (isInitialized && !isAuthenticated) {
      navigate('/auth');
    }
  }, [isInitialized, isAuthenticated, navigate]);

  // Show loading while global systems initialize
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  // Not authenticated - will redirect
  if (!isAuthenticated) {
    return null;
  }

  return <AureonDashboard />;
}
