import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import QuantumTradingConsole from '@/components/QuantumTradingConsole';
import { BinanceCredentialsSettings } from '@/components/BinanceCredentialsSettings';
import { TradingConfig } from '@/components/TradingConfig';
import { Activity, Settings, Sliders } from 'lucide-react';

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Tabs defaultValue="trading" className="w-full">
        <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4">
            <TabsList className="grid w-full max-w-md grid-cols-3 bg-muted/50">
              <TabsTrigger value="trading" className="gap-2">
                <Activity className="h-4 w-4" />
                Trading
              </TabsTrigger>
              <TabsTrigger value="config" className="gap-2">
                <Sliders className="h-4 w-4" />
                Config
              </TabsTrigger>
              <TabsTrigger value="credentials" className="gap-2">
                <Settings className="h-4 w-4" />
                API Keys
              </TabsTrigger>
            </TabsList>
          </div>
        </div>

        <TabsContent value="trading" className="m-0">
          <QuantumTradingConsole />
        </TabsContent>

        <TabsContent value="config" className="container mx-auto py-6 px-4">
          <TradingConfig />
        </TabsContent>

        <TabsContent value="credentials" className="container mx-auto py-6 px-4 max-w-2xl">
          <BinanceCredentialsSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Index;
