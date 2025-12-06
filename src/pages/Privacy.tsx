import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Privacy() {
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-3xl mx-auto">
        <Button variant="ghost" size="sm" asChild className="mb-6">
          <Link to="/auth" className="flex items-center gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Sign Up
          </Link>
        </Button>

        <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
        <p className="text-sm text-muted-foreground mb-8">Last updated: {new Date().toLocaleDateString()}</p>

        <div className="prose prose-sm prose-invert max-w-none space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-3">1. Information We Collect</h2>
            <p className="text-muted-foreground">
              We collect the following information when you register:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mt-2 space-y-1">
              <li><strong>Email address</strong> — for account authentication and notifications</li>
              <li><strong>Password</strong> — hashed using industry-standard bcrypt (we never see your plain password)</li>
              <li><strong>Exchange API credentials</strong> — encrypted with AES-256-GCM before storage</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">2. How We Protect Your Data</h2>
            <p className="text-muted-foreground">
              Your security is our priority. We implement multiple layers of protection:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mt-2 space-y-1">
              <li><strong>AES-256-GCM Encryption</strong> — Your API keys are encrypted before storage</li>
              <li><strong>Row Level Security (RLS)</strong> — Database policies ensure only you can access your data</li>
              <li><strong>TLS 1.3</strong> — All data in transit is encrypted</li>
              <li><strong>No Withdrawal Access</strong> — We never request or store withdrawal permissions</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">3. How We Use Your Data</h2>
            <p className="text-muted-foreground">
              Your data is used exclusively for:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mt-2 space-y-1">
              <li>Authenticating your account</li>
              <li>Connecting to your exchange accounts to execute trades</li>
              <li>Displaying your portfolio and trading history</li>
              <li>Sending important account notifications</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">4. Data Sharing</h2>
            <p className="text-muted-foreground">
              We do <strong className="text-foreground">NOT</strong> share, sell, or rent your personal data or API credentials to any third parties. Your credentials are only used to communicate with the exchanges you've connected.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">5. Data Retention</h2>
            <p className="text-muted-foreground">
              Your data is retained for as long as your account is active. You may request deletion of your account and all associated data at any time by contacting support.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">6. Your Rights</h2>
            <p className="text-muted-foreground">
              You have the right to:
            </p>
            <ul className="list-disc list-inside text-muted-foreground mt-2 space-y-1">
              <li>Access your personal data</li>
              <li>Request correction of inaccurate data</li>
              <li>Request deletion of your data</li>
              <li>Export your data in a portable format</li>
            </ul>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">7. Cookies</h2>
            <p className="text-muted-foreground">
              We use essential cookies only for authentication and session management. We do not use tracking or advertising cookies.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold mb-3">8. Contact</h2>
            <p className="text-muted-foreground">
              For privacy-related inquiries, please contact us through the platform's support channels.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
