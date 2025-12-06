import { TradingSettingsPanel } from '@/components/TradingSettingsPanel';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TradingSettings = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Trading Settings</h1>
            <p className="text-muted-foreground">Configure your Binance credentials and test live trading</p>
          </div>
        </div>

        <TradingSettingsPanel />
      </div>
    </div>
  );
};

export default TradingSettings;
