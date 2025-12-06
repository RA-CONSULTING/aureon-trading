import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "@/components/theme-provider";
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

const queryClient = new QueryClient();

const App = () => (
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
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </ThemeProvider>
);

export default App;
