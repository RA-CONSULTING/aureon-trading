import { useEffect, useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";
import { globalSystemsManager } from "@/core/globalSystemsManager";
import Index from "./pages/Index";
import Auth from "./pages/Auth";
import TradingSettings from "./pages/TradingSettings";
import NotFound from "./pages/NotFound";
import WarRoom from "./pages/WarRoom";
import Quantum from "./pages/Quantum";
import Prism from "./pages/Prism";
import Rainbow from "./pages/Rainbow";
import Earth from "./pages/Earth";
import Analytics from "./pages/Analytics";
import Portfolio from "./pages/Portfolio";
import Backtest from "./pages/Backtest";
import Settings from "./pages/Settings";
import Systems from "./pages/Systems";
import AdminKYC from "./pages/AdminKYC";
import Terms from "./pages/Terms";
import Privacy from "./pages/Privacy";

const queryClient = new QueryClient();

// Initialize global systems manager ONCE at app root
let systemsInitialized = false;

const App = () => {
  const [ready, setReady] = useState(systemsInitialized);
  
  useEffect(() => {
    if (!systemsInitialized) {
      systemsInitialized = true;
      console.log('🌌 App: Initializing GlobalSystemsManager...');
      
      globalSystemsManager.initialize().then(() => {
        console.log('✅ App: GlobalSystemsManager ready');
        setReady(true);
      }).catch((error) => {
        console.error('🚨 App: GlobalSystemsManager init failed:', error);
        setReady(true); // Force ready even on failure
      });
      
      // Failsafe: force ready after 15 seconds no matter what
      const failsafe = setTimeout(() => {
        if (!ready) {
          console.warn('⚠️ App: Initialization failsafe triggered after 15s');
          setReady(true);
        }
      }, 15000);
      
      return () => clearTimeout(failsafe);
    }
  }, [ready]);
  
  // Show loading while systems initialize (only on first load)
  if (!ready) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-muted-foreground">Initializing quantum systems...</p>
        </div>
      </div>
    );
  }
  
  return (
  <ThemeProvider defaultTheme="dark">
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/auth" element={<Auth />} />
            <Route path="/war-room" element={<WarRoom />} />
            <Route path="/quantum" element={<Quantum />} />
            <Route path="/prism" element={<Prism />} />
            <Route path="/rainbow" element={<Rainbow />} />
            <Route path="/earth" element={<Earth />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/portfolio" element={<Portfolio />} />
            <Route path="/backtest" element={<Backtest />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/settings/trading" element={<TradingSettings />} />
            <Route path="/systems" element={<Systems />} />
            <Route path="/admin/kyc" element={<AdminKYC />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
  );
};

export default App;
