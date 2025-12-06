import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { z } from "zod";
import PaymentGate from "@/components/PaymentGate";
import { Sparkles, Eye, EyeOff } from "lucide-react";

const emailSchema = z.string().email("Invalid email address");
const passwordSchema = z.string().min(8, "Password must be at least 8 characters");
const binanceApiKeySchema = z.string().min(10, "Binance API key is required");
const binanceApiSecretSchema = z.string().min(10, "Binance API secret is required");

const SUPER_USER_EMAIL = "gary@raconsultingandbrokerageservices.com";

export default function Auth() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPaymentGate, setShowPaymentGate] = useState(false);
  const [pendingUserId, setPendingUserId] = useState<string | null>(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showApiSecret, setShowApiSecret] = useState(false);
  
  // Sign In State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  // Sign Up State
  const [signUpEmail, setSignUpEmail] = useState("");
  const [signUpPassword, setSignUpPassword] = useState("");
  const [binanceApiKey, setBinanceApiKey] = useState("");
  const [binanceApiSecret, setBinanceApiSecret] = useState("");

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        checkUserStatus(session.user.id, session.user.email);
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        checkUserStatus(session.user.id, session.user.email);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const checkUserStatus = async (userId: string, userEmail: string | undefined) => {
    // Super user bypasses payment
    if (userEmail === SUPER_USER_EMAIL) {
      navigate("/");
      return;
    }

    // Check aureon_user_sessions for payment status
    const { data: session } = await supabase
      .from("aureon_user_sessions")
      .select("payment_completed")
      .eq("user_id", userId)
      .single();

    if (session?.payment_completed) {
      navigate("/");
    } else {
      setPendingUserId(userId);
      setShowPaymentGate(true);
    }
  };

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      emailSchema.parse(signUpEmail);
      passwordSchema.parse(signUpPassword);
      binanceApiKeySchema.parse(binanceApiKey);
      binanceApiSecretSchema.parse(binanceApiSecret);
      
      setLoading(true);

      // Create user account
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: signUpEmail,
        password: signUpPassword,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
        }
      });

      if (authError) throw authError;
      if (!authData.user) throw new Error("Failed to create account");

      // Create aureon_user_sessions record with encrypted Binance credentials
      try {
        const { error: sessionError } = await supabase.functions.invoke('create-aureon-session', {
          body: {
            userId: authData.user.id,
            apiKey: binanceApiKey,
            apiSecret: binanceApiSecret
          }
        });

        if (sessionError) {
          console.warn('Session creation via edge function failed, using fallback:', sessionError);
          throw sessionError;
        }
      } catch (fnError) {
        console.warn('Edge function failed, creating session directly:', fnError);
        // Fallback: create session directly with is_trading_active = true for auto-start
        const { error: insertError } = await supabase.from('aureon_user_sessions').insert({
          user_id: authData.user.id,
          payment_completed: false,
          is_trading_active: false,
          gas_tank_balance: 100,
          trading_mode: 'paper'
        });
        
        if (insertError) {
          console.error('Fallback session creation failed:', insertError);
        }
      }

      // Super user bypasses payment
      if (authData.user.email === SUPER_USER_EMAIL) {
        await supabase
          .from("aureon_user_sessions")
          .update({ payment_completed: true, payment_completed_at: new Date().toISOString() })
          .eq("user_id", authData.user.id);
        
        toast.success("Welcome! Redirecting...");
        setTimeout(() => navigate("/"), 1000);
      } else {
        toast.success("Account created! Please complete payment.");
        setPendingUserId(authData.user.id);
        setShowPaymentGate(true);
      }
      
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
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) throw error;

      // Super user bypasses payment
      if (data.user.email === SUPER_USER_EMAIL) {
        toast.success("Welcome back!");
        navigate("/");
        return;
      }

      // Check payment status
      const { data: session } = await supabase
        .from("aureon_user_sessions")
        .select("payment_completed")
        .eq("user_id", data.user.id)
        .single();

      if (!session?.payment_completed) {
        toast.info("Please complete payment to access");
        setPendingUserId(data.user.id);
        setShowPaymentGate(true);
        return;
      }

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

  const handlePaymentComplete = async () => {
    if (!pendingUserId) return;

    await supabase
      .from("aureon_user_sessions")
      .update({
        payment_completed: true,
        payment_completed_at: new Date().toISOString()
      })
      .eq("user_id", pendingUserId);

    toast.success("Welcome to AUREON!");
    setTimeout(() => navigate("/"), 1000);
  };

  if (showPaymentGate && pendingUserId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <PaymentGate userId={pendingUserId} onPaymentComplete={handlePaymentComplete} />
      </div>
    );
  }

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
              <form onSubmit={handleSignUp} className="space-y-4">
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

                <div className="border-t border-border/50 pt-4 mt-4">
                  <p className="text-xs text-muted-foreground mb-3">
                    Binance API credentials (encrypted & secure)
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