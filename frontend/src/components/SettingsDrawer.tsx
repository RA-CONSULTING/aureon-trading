import { useState } from "react";
import { Button } from "@/components/ui/button";
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
import { Info, FileText, Shield } from "lucide-react";

export function SettingsDrawer() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon">
          <Info className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>About AUREON</SheetTitle>
          <SheetDescription>
            Live trading feed from the AUREON Quantum Trading System
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* System Info */}
          <div className="p-4 rounded-lg bg-muted/50 space-y-2">
            <h3 className="font-medium text-foreground">Live Feed Status</h3>
            <p className="text-sm text-muted-foreground">
              This dashboard displays real-time trading data from the AUREON system. 
              Data is pushed from the Python terminal every 10 seconds.
            </p>
            <div className="flex items-center gap-2 mt-3">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-green-500 font-medium">Connected to Live Feed</span>
            </div>
          </div>

          <Accordion type="single" collapsible className="w-full">
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
                    <h4 className="font-medium text-foreground mb-1">4. Information Only</h4>
                    <p>This live feed is for informational purposes only. It displays the trading activity of the AUREON system but does not constitute financial advice.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">5. No Financial Advice</h4>
                    <p>The Service does not provide financial, investment, or trading advice. You are solely responsible for your own trading decisions.</p>
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
                    <p>This is a public live feed. We do not collect any personal information from viewers.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">2. How We Protect Data</h4>
                    <ul className="list-disc list-inside space-y-1">
                      <li>TLS 1.3 for all data in transit</li>
                      <li>No personal data collection from viewers</li>
                      <li>Trading data displayed is from the system operator only</li>
                    </ul>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">3. Data Sharing</h4>
                    <p>We do NOT share, sell, or rent any viewer data to third parties.</p>
                  </div>

                  <div>
                    <h4 className="font-medium text-foreground mb-1">4. Cookies</h4>
                    <p>This site may use minimal cookies for theme preferences only. No tracking cookies are used.</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Footer */}
          <div className="pt-4 border-t border-border text-center">
            <p className="text-xs text-muted-foreground">
              AUREON Quantum Trading System v3.0
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              © {new Date().getFullYear()} Gary Leckey
            </p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}