import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import QuantumTradingConsole from '@/components/QuantumTradingConsole';
import WarRoomDashboard from '@/components/WarRoomDashboard';
import { BinanceCredentialsSettings } from '@/components/BinanceCredentialsSettings';
import { BinanceCredentialsAdmin } from '@/components/BinanceCredentialsAdmin';
import { TradingConfig } from '@/components/TradingConfig';
import HNCImperialDetection from '@/components/HNCImperialDetection';
import { Activity, Settings, Sliders, Shield, Flame, Radio } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Tabs defaultValue="trading" className="w-full">
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4">
            <TabsList className="grid w-full max-w-4xl grid-cols-6 bg-muted/50">
              <TabsTrigger value="trading" className="gap-2">
                <Activity className="h-4 w-4" />
                Trading
              </TabsTrigger>
              <TabsTrigger value="warroom" className="gap-2">
                <Flame className="h-4 w-4" />
                War Room
              </TabsTrigger>
              <TabsTrigger value="hnc-detection" className="gap-2">
                <Radio className="h-4 w-4" />
                HNC Detection
              </TabsTrigger>
              <TabsTrigger value="config" className="gap-2">
                <Sliders className="h-4 w-4" />
                Config
              </TabsTrigger>
              <TabsTrigger value="credentials" className="gap-2">
                <Settings className="h-4 w-4" />
                API Keys
              </TabsTrigger>
              <TabsTrigger value="admin" className="gap-2">
                <Shield className="h-4 w-4" />
                Manage Bots
              </TabsTrigger>
            </TabsList>
          </div>
        </div>

        <TabsContent value="trading" className="m-0">
          <QuantumTradingConsole />
        </TabsContent>

        <TabsContent value="warroom" className="m-0">
          <WarRoomDashboard />
        </TabsContent>

        <TabsContent value="hnc-detection" className="m-0">
          <HNCImperialDetection />
        </TabsContent>

        <TabsContent value="config" className="container mx-auto py-6 px-4">
          <TradingConfig />
        </TabsContent>

        <TabsContent value="credentials" className="container mx-auto py-6 px-4 max-w-2xl">
          <BinanceCredentialsSettings />
        </TabsContent>

        <TabsContent value="admin" className="container mx-auto py-6 px-4 max-w-4xl">
          <BinanceCredentialsAdmin />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Index;
