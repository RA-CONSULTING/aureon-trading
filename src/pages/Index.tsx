import { useState, lazy, Suspense } from 'react';
import { cn } from '@/lib/utils';
import QuantumTradingConsole from '@/components/QuantumTradingConsole';
import WarRoomDashboard from '@/components/WarRoomDashboard';
import { BinanceCredentialsSettings } from '@/components/BinanceCredentialsSettings';
import { BinanceCredentialsAdmin } from '@/components/BinanceCredentialsAdmin';
import { TradingConfig } from '@/components/TradingConfig';
import HNCImperialDetection from '@/components/HNCImperialDetection';
import SystemsIntegrationDashboard from '@/components/SystemsIntegrationDashboard';
import { Activity, Settings, Sliders, Shield, Flame, Radio, Sparkles, Orbit, Gauge, Compass, Network } from 'lucide-react';

const navItems = [
  { id: 'trading', label: 'Trading', icon: Activity },
  { id: 'warroom', label: 'War Room', icon: Flame },
  { id: 'systems', label: 'Systems', icon: Network },
  { id: 'hnc-detection', label: 'HNC', icon: Radio },
  { id: 'config', label: 'Config', icon: Sliders },
  { id: 'credentials', label: 'API Keys', icon: Settings },
  { id: 'admin', label: 'Bots', icon: Shield },
];

const Index = () => {
  const [activeTab, setActiveTab] = useState('trading');

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/90 backdrop-blur-xl">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="h-9 w-9 rounded-lg bg-gradient-prism flex items-center justify-center love-pulse">
                  <Sparkles className="h-4 w-4 text-primary-foreground" />
                </div>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold text-prism">AUREON</h1>
                <p className="text-[9px] text-muted-foreground tracking-widest uppercase -mt-0.5">
                  528 Hz · The Prism
                </p>
              </div>
            </div>

            {/* Navigation */}
            <nav className="flex items-center gap-0.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={cn(
                      "relative px-3 py-1.5 rounded-md transition-all duration-200",
                      isActive 
                        ? "bg-primary/15 text-primary" 
                        : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                    )}
                  >
                    <div className="flex items-center gap-1.5">
                      <Icon className="h-3.5 w-3.5" />
                      <span className="text-xs font-medium hidden md:inline">{item.label}</span>
                    </div>
                    {isActive && (
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-primary rounded-full" />
                    )}
                  </button>
                );
              })}
            </nav>

            {/* Status */}
            <div className="flex items-center gap-2">
              <div className="h-1.5 w-1.5 rounded-full bg-primary love-pulse" />
              <span className="text-[10px] text-muted-foreground hidden lg:block font-mono">LIVE</span>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <main className="animate-fade-in">
        {activeTab === 'trading' && <QuantumTradingConsole />}
        {activeTab === 'warroom' && <WarRoomDashboard />}
        {activeTab === 'systems' && <SystemsIntegrationDashboard />}
        {activeTab === 'hnc-detection' && <HNCImperialDetection />}
        {activeTab === 'config' && (
          <div className="container mx-auto py-6 px-4">
            <TradingConfig />
          </div>
        )}
        {activeTab === 'credentials' && (
          <div className="container mx-auto py-6 px-4 max-w-2xl">
            <BinanceCredentialsSettings />
          </div>
        )}
        {activeTab === 'admin' && (
          <div className="container mx-auto py-6 px-4 max-w-4xl">
            <BinanceCredentialsAdmin />
          </div>
        )}
      </main>
    </div>
  );
};

export default Index;
