import { useState } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Settings, Key, Bell, FileText, Shield, LogOut, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";

interface SettingsDrawerProps {
  onLogout: () => void;
}

export function SettingsDrawer({ onLogout }: SettingsDrawerProps) {
  const [open, setOpen] = useState(false);
  const [binanceApiKey, setBinanceApiKey] = useState("");
  const [binanceApiSecret, setBinanceApiSecret] = useState("");
  const [showSecret, setShowSecret] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleLogout = async () => {
    await supabase.auth.signOut();
    toast.success("Logged out");
    setOpen(false);
    onLogout();
  };

  const saveCredentials = async () => {
    if (!binanceApiKey || !binanceApiSecret) {
      toast.error("Please enter both API key and secret");
      return;
    }

    setSaving(true);
    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) throw new Error("Not authenticated");

      const { error } = await supabase.functions.invoke('update-user-credentials', {
        body: {
          userId: user.id,
          binanceApiKey,
          binanceApiSecret,
        }
      });

      if (error) throw error;
      toast.success("Credentials saved");
      setBinanceApiKey("");
      setBinanceApiSecret("");
    } catch (error: any) {
      toast.error(error.message || "Failed to save credentials");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon">
          <Settings className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Settings</SheetTitle>
          <SheetDescription>
            Manage your account and preferences
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          <Accordion type="single" collapsible className="w-full">
            {/* API Credentials */}
            <AccordionItem value="credentials">
              <AccordionTrigger className="text-sm">
                <span className="flex items-center gap-2">
                  <Key className="h-4 w-4" />
                  API Credentials
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-4 pt-2">
                  <div className="space-y-2">
                    <Label htmlFor="api-key">Binance API Key</Label>
                    <Input
                      id="api-key"
                      type="text"
                      placeholder="Enter your API key"
                      value={binanceApiKey}
                      onChange={(e) => setBinanceApiKey(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="api-secret">Binance API Secret</Label>
                    <div className="relative">
                      <Input
                        id="api-secret"
                        type={showSecret ? "text" : "password"}
                        placeholder="Enter your API secret"
                        value={binanceApiSecret}
                        onChange={(e) => setBinanceApiSecret(e.target.value)}
                      />
                      <button
                        type="button"
                        onClick={() => setShowSecret(!showSecret)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      >
                        {showSecret ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                  </div>
                  <Button onClick={saveCredentials} disabled={saving} className="w-full">
                    {saving ? "Saving..." : "Save Credentials"}
                  </Button>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Alerts */}
            <AccordionItem value="alerts">
              <AccordionTrigger className="text-sm">
                <span className="flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  Alerts & Notifications
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <p className="text-sm text-muted-foreground py-4">
                  Alert settings coming soon. Configure price alerts, coherence thresholds, and notification preferences.
                </p>
              </AccordionContent>
            </AccordionItem>

            {/* Terms of Service */}
            <AccordionItem value="terms">
              <AccordionTrigger className="text-sm">
                <span className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Terms of Service
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="text-sm text-muted-foreground space-y-4 py-2 max-h-[300px] overflow-y-auto">
                  <p className="text-xs">Last updated: {new Date().toLocaleDateString()}</p>
                  
                  <div>
                    <h4 className="font-medium text-foreground mb-1">1. Acceptance of Terms</h4>
                    <p>By accessing and using AUREON Quantum Trading System, you agree to be bound by these Terms of Service.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">2. Description of Service</h4>
                    <p>AUREON is an autonomous algorithmic trading system that connects to cryptocurrency exchanges via API to execute trades.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">3. Risk Disclosure</h4>
                    <p><strong className="text-destructive">IMPORTANT:</strong> Trading cryptocurrencies involves substantial risk of loss. You could lose some or all of your investment.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">4. API Credentials</h4>
                    <p>You are responsible for the security of your exchange API credentials. We encrypt your credentials using AES-256-GCM encryption.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">5. No Financial Advice</h4>
                    <p>The Service does not provide financial, investment, or trading advice. You are solely responsible for your trading activities.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">6. Limitation of Liability</h4>
                    <p>AUREON shall not be liable for any trading losses, system downtime, or any other damages arising from use of the Service.</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            {/* Privacy Policy */}
            <AccordionItem value="privacy">
              <AccordionTrigger className="text-sm">
                <span className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Privacy Policy
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="text-sm text-muted-foreground space-y-4 py-2 max-h-[300px] overflow-y-auto">
                  <p className="text-xs">Last updated: {new Date().toLocaleDateString()}</p>
                  
                  <div>
                    <h4 className="font-medium text-foreground mb-1">1. Information We Collect</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Email address — for account authentication</li>
                      <li>Password — hashed using bcrypt</li>
                      <li>Exchange API credentials — encrypted with AES-256-GCM</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">2. How We Protect Your Data</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>AES-256-GCM Encryption for API keys</li>
                      <li>Row Level Security (RLS) policies</li>
                      <li>TLS 1.3 for all data in transit</li>
                      <li>No withdrawal access ever requested</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">3. Data Sharing</h4>
                    <p>We do NOT share, sell, or rent your personal data or API credentials to any third parties.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">4. Your Rights</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>Access your personal data</li>
                      <li>Request correction of inaccurate data</li>
                      <li>Request deletion of your data</li>
                      <li>Export your data in a portable format</li>
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Logout Button */}
          <div className="pt-4 border-t border-border">
            <Button variant="destructive" onClick={handleLogout} className="w-full">
              <LogOut className="h-4 w-4 mr-2" />
              Log Out
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
