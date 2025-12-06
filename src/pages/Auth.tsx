import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { toast } from "sonner";
import { z } from "zod";
import { Sparkles, Eye, EyeOff, ChevronDown, ChevronUp } from "lucide-react";

const emailSchema = z.string().email("Invalid email address");
const passwordSchema = z.string().min(8, "Password must be at least 8 characters");
const binanceApiKeySchema = z.string().min(10, "Binance API key is required");
const binanceApiSecretSchema = z.string().min(10, "Binance API secret is required");

export default function Auth() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [showOtherExchanges, setShowOtherExchanges] = useState(false);
  
  // Sign In State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  // Sign Up State
  const [signUpEmail, setSignUpEmail] = useState("");
  const [signUpPassword, setSignUpPassword] = useState("");
  const [binanceApiKey, setBinanceApiKey] = useState("");
  const [binanceApiSecret, setBinanceApiSecret] = useState("");
  
  // Optional exchange credentials
  const [krakenApiKey, setKrakenApiKey] = useState("");
  const [krakenApiSecret, setKrakenApiSecret] = useState("");
  const [alpacaApiKey, setAlpacaApiKey] = useState("");
  const [alpacaSecretKey, setAlpacaSecretKey] = useState("");
  const [capitalApiKey, setCapitalApiKey] = useState("");
  const [capitalPassword, setCapitalPassword] = useState("");
  const [capitalIdentifier, setCapitalIdentifier] = useState("");

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        navigate("/");
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        navigate("/");
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      emailSchema.parse(signUpEmail);
      passwordSchema.parse(signUpPassword);
      binanceApiKeySchema.parse(binanceApiKey);
      binanceApiSecretSchema.parse(binanceApiSecret);
      
      setLoading(true);

      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: signUpEmail,
        password: signUpPassword,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
        }
      });

      if (authError) throw authError;
      if (!authData.user) throw new Error("Failed to create account");

      try {
        const { error: sessionError } = await supabase.functions.invoke('create-aureon-session', {
          body: {
            userId: authData.user.id,
            // Binance (required)
            apiKey: binanceApiKey,
            apiSecret: binanceApiSecret,
            // Kraken (optional)
            krakenApiKey: krakenApiKey || null,
            krakenApiSecret: krakenApiSecret || null,
            // Alpaca (optional)
            alpacaApiKey: alpacaApiKey || null,
            alpacaSecretKey: alpacaSecretKey || null,
            // Capital.com (optional)
            capitalApiKey: capitalApiKey || null,
            capitalPassword: capitalPassword || null,
            capitalIdentifier: capitalIdentifier || null
          }
        });

        if (sessionError) {
          console.warn('Session creation via edge function failed, using fallback:', sessionError);
          throw sessionError;
        }
        
        await supabase
          .from("aureon_user_sessions")
          .update({ payment_completed: true, payment_completed_at: new Date().toISOString() })
          .eq("user_id", authData.user.id);
          
      } catch (fnError) {
        console.warn('Edge function failed, creating session directly:', fnError);
        const { error: insertError } = await supabase.from('aureon_user_sessions').insert({
          user_id: authData.user.id,
          payment_completed: true,
          payment_completed_at: new Date().toISOString(),
          is_trading_active: false,
          gas_tank_balance: 100,
          trading_mode: 'paper'
        });
        
        if (insertError) {
          console.error('Fallback session creation failed:', insertError);
        }
      }

      toast.success("Account created! Welcome to AUREON.");
      setTimeout(() => navigate("/"), 1000);
      
    } catch (error) {
      if (error instanceof z.ZodError) {
        toast.error(error.errors[0].message);
      } else if (error instanceof Error) {
        toast.error(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      emailSchema.parse(email);
      passwordSchema.parse(password);
      
      setLoading(true);
      
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) throw error;

      toast.success("Welcome back!");
      navigate("/");
    } catch (error) {
      if (error instanceof z.ZodError) {
        toast.error(error.errors[0].message);
      } else if (error instanceof Error) {
        toast.error(error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md border-border/50">
        <CardHeader className="text-center space-y-2">
          <div className="flex justify-center">
            <div className="h-12 w-12 rounded-xl bg-gradient-prism flex items-center justify-center love-pulse">
              <Sparkles className="h-6 w-6 text-primary-foreground" />
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-prism">AUREON</CardTitle>
          <CardDescription>Autonomous Quantum Trading</CardDescription>
        </CardHeader>
        
        <CardContent>
          <Tabs defaultValue="signin" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="signin">Sign In</TabsTrigger>
              <TabsTrigger value="signup">Sign Up</TabsTrigger>
            </TabsList>
            
            <TabsContent value="signin">
              <form onSubmit={handleSignIn} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="signin-email">Email</Label>
                  <Input
                    id="signin-email"
                    type="email"
                    placeholder="your@email.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="signin-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="signin-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Signing in..." : "Sign In"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                <div className="space-y-2">
                  <Label htmlFor="signup-email">Email</Label>
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="your@email.com"
                    value={signUpEmail}
                    onChange={(e) => setSignUpEmail(e.target.value)}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="signup-password">Password</Label>
                  <div className="relative">
                    <Input
                      id="signup-password"
                      type={showPassword ? "text" : "password"}
                      placeholder="Min. 8 characters"
                      value={signUpPassword}
                      onChange={(e) => setSignUpPassword(e.target.value)}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Binance - Required */}
                <div className="border-t border-border/50 pt-4 mt-4">
                  <p className="text-xs text-muted-foreground mb-3">
                    Binance API credentials (required, encrypted & secure)
                  </p>
                  
                  <div className="space-y-3">
                    <div className="space-y-2">
                      <Label htmlFor="binance-api-key">API Key</Label>
                      <Input
                        id="binance-api-key"
                        type="text"
                        placeholder="Your Binance API Key"
                        value={binanceApiKey}
                        onChange={(e) => setBinanceApiKey(e.target.value)}
                        required
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="binance-api-secret">API Secret</Label>
                      <div className="relative">
                        <Input
                          id="binance-api-secret"
                          type={showApiSecret ? "text" : "password"}
                          placeholder="Your Binance API Secret"
                          value={binanceApiSecret}
                          onChange={(e) => setBinanceApiSecret(e.target.value)}
                          required
                        />
                        <button
                          type="button"
                          onClick={() => setShowApiSecret(!showApiSecret)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          {showApiSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Other Exchanges - Optional */}
                <Collapsible open={showOtherExchanges} onOpenChange={setShowOtherExchanges}>
                  <CollapsibleTrigger asChild>
                    <Button variant="ghost" className="w-full justify-between text-muted-foreground text-sm">
                      Add Other Exchanges (Optional)
                      {showOtherExchanges ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </Button>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="space-y-4 pt-2">
                    {/* Kraken */}
                    <div className="border border-border/30 rounded-lg p-3 space-y-3">
                      <p className="text-xs font-medium text-muted-foreground">Kraken</p>
                      <div className="space-y-2">
                        <Label htmlFor="kraken-api-key" className="text-xs">API Key</Label>
                        <Input
                          id="kraken-api-key"
                          type="text"
                          placeholder="Kraken API Key"
                          value={krakenApiKey}
                          onChange={(e) => setKrakenApiKey(e.target.value)}
                          className="h-9"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="kraken-api-secret" className="text-xs">API Secret</Label>
                        <Input
                          id="kraken-api-secret"
                          type="password"
                          placeholder="Kraken API Secret"
                          value={krakenApiSecret}
                          onChange={(e) => setKrakenApiSecret(e.target.value)}
                          className="h-9"
                        />
                      </div>
                    </div>

                    {/* Alpaca */}
                    <div className="border border-border/30 rounded-lg p-3 space-y-3">
                      <p className="text-xs font-medium text-muted-foreground">Alpaca (US Stocks)</p>
                      <div className="space-y-2">
                        <Label htmlFor="alpaca-api-key" className="text-xs">API Key</Label>
                        <Input
                          id="alpaca-api-key"
                          type="text"
                          placeholder="Alpaca API Key"
                          value={alpacaApiKey}
                          onChange={(e) => setAlpacaApiKey(e.target.value)}
                          className="h-9"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="alpaca-secret-key" className="text-xs">Secret Key</Label>
                        <Input
                          id="alpaca-secret-key"
                          type="password"
                          placeholder="Alpaca Secret Key"
                          value={alpacaSecretKey}
                          onChange={(e) => setAlpacaSecretKey(e.target.value)}
                          className="h-9"
                        />
                      </div>
                    </div>

                    {/* Capital.com */}
                    <div className="border border-border/30 rounded-lg p-3 space-y-3">
                      <p className="text-xs font-medium text-muted-foreground">Capital.com (CFDs)</p>
                      <div className="space-y-2">
                        <Label htmlFor="capital-api-key" className="text-xs">API Key</Label>
                        <Input
                          id="capital-api-key"
                          type="text"
                          placeholder="Capital.com API Key"
                          value={capitalApiKey}
                          onChange={(e) => setCapitalApiKey(e.target.value)}
                          className="h-9"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="capital-identifier" className="text-xs">Identifier (Email)</Label>
                        <Input
                          id="capital-identifier"
                          type="text"
                          placeholder="Your Capital.com Email"
                          value={capitalIdentifier}
                          onChange={(e) => setCapitalIdentifier(e.target.value)}
                          className="h-9"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="capital-password" className="text-xs">Password</Label>
                        <Input
                          id="capital-password"
                          type="password"
                          placeholder="Capital.com Password"
                          value={capitalPassword}
                          onChange={(e) => setCapitalPassword(e.target.value)}
                          className="h-9"
                        />
                      </div>
                    </div>
                  </CollapsibleContent>
                </Collapsible>

                <Button type="submit" className="w-full" disabled={loading}>
                  {loading ? "Creating account..." : "Create Account"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
