import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Terms() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-3xl mx-auto">
        <Button variant="ghost" size="sm" asChild className="mb-6">
          <Link to="/auth" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Sign Up
          </Link>
        </Button>

        <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>
        <p className="text-sm text-muted-foreground mb-8">Last updated: {new Date().toLocaleDateString()}</p>

        <div className="prose prose-sm prose-invert max-w-none space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-3">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground">
              By accessing and using AUREON Quantum Trading System ("the Service"), you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">2. Description of Service</h2>
            <p className="text-muted-foreground">
              AUREON is an autonomous algorithmic trading system that connects to cryptocurrency exchanges via API to execute trades based on quantum-inspired algorithms. The Service operates automatically once activated.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">3. Risk Disclosure</h2>
            <p className="text-muted-foreground">
              <strong className="text-foreground">IMPORTANT:</strong> Trading cryptocurrencies and other financial instruments involves substantial risk of loss. Past performance is not indicative of future results. You could lose some or all of your investment. Only trade with funds you can afford to lose completely.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">4. API Credentials</h2>
            <p className="text-muted-foreground">
              You are responsible for the security of your exchange API credentials. We encrypt your credentials using AES-256-GCM encryption. Never enable withdrawal permissions on API keys used with this Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">5. No Financial Advice</h2>
            <p className="text-muted-foreground">
              The Service does not provide financial, investment, or trading advice. All trading decisions are made by the autonomous system based on algorithmic signals. You are solely responsible for your trading activities.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">6. Limitation of Liability</h2>
            <p className="text-muted-foreground">
              To the maximum extent permitted by law, AUREON and its operators shall not be liable for any trading losses, system downtime, or any other damages arising from use of the Service.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">7. Modifications</h2>
            <p className="text-muted-foreground">
              We reserve the right to modify these terms at any time. Continued use of the Service after changes constitutes acceptance of the new terms.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">8. Contact</h2>
            <p className="text-muted-foreground">
              For questions about these Terms, please contact us through the platform's support channels.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
