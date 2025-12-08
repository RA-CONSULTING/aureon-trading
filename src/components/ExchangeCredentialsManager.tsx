import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';
import { Eye, EyeOff, Key, CheckCircle2, XCircle, RefreshCw, Save, Zap, Loader2 } from 'lucide-react';

interface ExchangeStatus {
  binance: boolean;
  kraken: boolean;
  alpaca: boolean;
  capital: boolean;
}

interface TestResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

export function ExchangeCredentialsManager() {
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, TestResult>>({});
  const [status, setStatus] = useState<ExchangeStatus>({
    binance: false,
    kraken: false,
    alpaca: false,
    capital: false
  });

  // Credential inputs
  const [binanceApiKey, setBinanceApiKey] = useState('');
  const [binanceApiSecret, setBinanceApiSecret] = useState('');
  const [krakenApiKey, setKrakenApiKey] = useState('');
  const [krakenApiSecret, setKrakenApiSecret] = useState('');
  const [alpacaApiKey, setAlpacaApiKey] = useState('');
  const [alpacaSecretKey, setAlpacaSecretKey] = useState('');
  const [capitalApiKey, setCapitalApiKey] = useState('');
  const [capitalPassword, setCapitalPassword] = useState('');
  const [capitalIdentifier, setCapitalIdentifier] = useState('');

  // Visibility toggles
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  useEffect(() => {
    checkExistingCredentials();
  }, []);

  const checkExistingCredentials = async () => {
    setChecking(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const { data } = await supabase
        .from('aureon_user_sessions')
        .select('binance_api_key_encrypted, kraken_api_key_encrypted, alpaca_api_key_encrypted, capital_api_key_encrypted')
        .eq('user_id', session.user.id)
        .single();

      if (data) {
        setStatus({
          binance: !!data.binance_api_key_encrypted,
          kraken: !!data.kraken_api_key_encrypted,
          alpaca: !!data.alpaca_api_key_encrypted,
          capital: !!data.capital_api_key_encrypted
        });
      }
    } catch (err) {
      console.error('Error checking credentials:', err);
    } finally {
      setChecking(false);
    }
  };

  const testConnection = async (exchange: string) => {
    let apiKey = '';
    let apiSecret = '';
    let identifier = '';
    let password = '';

    switch (exchange) {
      case 'binance':
        apiKey = binanceApiKey;
        apiSecret = binanceApiSecret;
        break;
      case 'kraken':
        apiKey = krakenApiKey;
        apiSecret = krakenApiSecret;
        break;
      case 'alpaca':
        apiKey = alpacaApiKey;
        apiSecret = alpacaSecretKey;
        break;
      case 'capital':
        apiKey = capitalApiKey;
        password = capitalPassword;
        identifier = capitalIdentifier;
        break;
    }

    if (!apiKey || (!apiSecret && exchange !== 'capital') || (exchange === 'capital' && !password)) {
      toast.error('Please enter credentials first');
      return;
    }

    setTesting(exchange);
    try {
      const { data, error } = await supabase.functions.invoke('test-exchange-connection', {
        body: { exchange, apiKey, apiSecret, identifier, password }
      });

      if (error) throw error;

      setTestResults(prev => ({ ...prev, [exchange]: data }));

      if (data.success) {
        toast.success(`${exchange} connection verified!`);
      } else {
        toast.error(data.message || `${exchange} connection failed`);
      }
    } catch (err) {
      console.error('Connection test error:', err);
      setTestResults(prev => ({ 
        ...prev, 
        [exchange]: { success: false, message: 'Test failed - network error' } 
      }));
      toast.error('Connection test failed');
    } finally {
      setTesting(null);
    }
  };

  const handleSaveCredentials = async (exchange: string) => {
    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast.error('Please sign in first');
        return;
      }

      let body: Record<string, string> = {};

      switch (exchange) {
        case 'binance':
          if (!binanceApiKey || !binanceApiSecret) {
            toast.error('Both API Key and Secret are required');
            return;
          }
          body = { binanceApiKey, binanceApiSecret };
          break;
        case 'kraken':
          if (!krakenApiKey || !krakenApiSecret) {
            toast.error('Both API Key and Secret are required');
            return;
          }
          body = { krakenApiKey, krakenApiSecret };
          break;
        case 'alpaca':
          if (!alpacaApiKey || !alpacaSecretKey) {
            toast.error('Both API Key and Secret are required');
            return;
          }
          body = { alpacaApiKey, alpacaSecretKey };
          break;
        case 'capital':
          if (!capitalApiKey || !capitalPassword) {
            toast.error('API Key and Password are required');
            return;
          }
          body = { capitalApiKey, capitalPassword, capitalIdentifier };
          break;
      }

      const { data, error } = await supabase.functions.invoke('update-user-credentials', {
        body
      });

      if (error) throw error;

      toast.success(`${exchange.charAt(0).toUpperCase() + exchange.slice(1)} credentials saved`);
      
      // Clear inputs and refresh status
      switch (exchange) {
        case 'binance':
          setBinanceApiKey('');
          setBinanceApiSecret('');
          break;
        case 'kraken':
          setKrakenApiKey('');
          setKrakenApiSecret('');
          break;
        case 'alpaca':
          setAlpacaApiKey('');
          setAlpacaSecretKey('');
          break;
        case 'capital':
          setCapitalApiKey('');
          setCapitalPassword('');
          setCapitalIdentifier('');
          break;
      }
      
      // Clear test result for this exchange
      setTestResults(prev => {
        const updated = { ...prev };
        delete updated[exchange];
        return updated;
      });
      
      await checkExistingCredentials();
    } catch (err) {
      console.error('Error saving credentials:', err);
      toast.error('Failed to save credentials. Please check encryption key configuration.');
    } finally {
      setLoading(false);
    }
  };

  const toggleSecret = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const ExchangeCard = ({ 
    name, 
    label, 
    description,
    isConnected,
    apiKeyValue,
    apiKeyOnChange,
    secretValue,
    secretOnChange,
    secretLabel = 'API Secret',
    secretKey,
    extraFields
  }: {
    name: string;
    label: string;
    description: string;
    isConnected: boolean;
    apiKeyValue: string;
    apiKeyOnChange: (v: string) => void;
    secretValue: string;
    secretOnChange: (v: string) => void;
    secretLabel?: string;
    secretKey: string;
    extraFields?: React.ReactNode;
  }) => {
    const testResult = testResults[name];
    const isTesting = testing === name;

    return (
      <Card className={`border ${isConnected ? 'border-green-500/30 bg-green-500/5' : 'border-border'}`}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Key className="h-4 w-4" />
                {label}
              </CardTitle>
              <CardDescription className="text-xs">{description}</CardDescription>
            </div>
            <Badge variant={isConnected ? 'default' : 'secondary'} className={isConnected ? 'bg-green-500' : ''}>
              {isConnected ? (
                <><CheckCircle2 className="h-3 w-3 mr-1" /> Connected</>
              ) : (
                <><XCircle className="h-3 w-3 mr-1" /> Not Connected</>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label className="text-xs">API Key</Label>
            <Input
              type="text"
              placeholder={isConnected ? '••••••••' : 'Enter API Key'}
              value={apiKeyValue}
              onChange={(e) => apiKeyOnChange(e.target.value)}
              className="h-9"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-xs">{secretLabel}</Label>
            <div className="relative">
              <Input
                type={showSecrets[secretKey] ? 'text' : 'password'}
                placeholder={isConnected ? '••••••••' : `Enter ${secretLabel}`}
                value={secretValue}
                onChange={(e) => secretOnChange(e.target.value)}
                className="h-9 pr-10"
              />
              <button
                type="button"
                onClick={() => toggleSecret(secretKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showSecrets[secretKey] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>
          {extraFields}
          
          {/* Test result display */}
          {testResult && (
            <div className={`text-xs p-2 rounded ${testResult.success ? 'bg-green-500/10 text-green-500' : 'bg-destructive/10 text-destructive'}`}>
              {testResult.success ? '✓' : '✗'} {testResult.message}
            </div>
          )}
          
          <div className="flex gap-2">
            <Button 
              onClick={() => testConnection(name)} 
              disabled={isTesting || loading}
              variant="outline"
              size="sm"
              className="flex-1"
            >
              {isTesting ? (
                <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Testing...</>
              ) : (
                <><Zap className="h-4 w-4 mr-2" /> Test</>
              )}
            </Button>
            <Button 
              onClick={() => handleSaveCredentials(name)} 
              disabled={loading || isTesting}
              size="sm"
              className="flex-1"
            >
              <Save className="h-4 w-4 mr-2" />
              {isConnected ? 'Update' : 'Save'}
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (checking) {
    return (
      <div className="flex items-center justify-center p-8">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const connectedCount = Object.values(status).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Exchange Connections</h3>
          <p className="text-sm text-muted-foreground">
            {connectedCount}/4 exchanges connected
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={checkExistingCredentials}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ExchangeCard
          name="binance"
          label="Binance"
          description="Primary crypto exchange"
          isConnected={status.binance}
          apiKeyValue={binanceApiKey}
          apiKeyOnChange={setBinanceApiKey}
          secretValue={binanceApiSecret}
          secretOnChange={setBinanceApiSecret}
          secretKey="binance"
        />

        <ExchangeCard
          name="kraken"
          label="Kraken"
          description="Crypto exchange (GBP/EUR)"
          isConnected={status.kraken}
          apiKeyValue={krakenApiKey}
          apiKeyOnChange={setKrakenApiKey}
          secretValue={krakenApiSecret}
          secretOnChange={setKrakenApiSecret}
          secretKey="kraken"
        />

        <ExchangeCard
          name="alpaca"
          label="Alpaca"
          description="US Stocks & Crypto"
          isConnected={status.alpaca}
          apiKeyValue={alpacaApiKey}
          apiKeyOnChange={setAlpacaApiKey}
          secretValue={alpacaSecretKey}
          secretOnChange={setAlpacaSecretKey}
          secretKey="alpaca"
        />

        <ExchangeCard
          name="capital"
          label="Capital.com"
          description="CFDs & Forex"
          isConnected={status.capital}
          apiKeyValue={capitalApiKey}
          apiKeyOnChange={setCapitalApiKey}
          secretValue={capitalPassword}
          secretOnChange={setCapitalPassword}
          secretLabel="Password"
          secretKey="capital"
          extraFields={
            <div className="space-y-2">
              <Label className="text-xs">Identifier (optional)</Label>
              <Input
                type="text"
                placeholder="Account Identifier"
                value={capitalIdentifier}
                onChange={(e) => setCapitalIdentifier(e.target.value)}
                className="h-9"
              />
            </div>
          }
        />
      </div>
    </div>
  );
}
