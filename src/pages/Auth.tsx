import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { z } from "zod";

const emailSchema = z.string().email("Invalid email address");
const passwordSchema = z.string().min(8, "Password must be at least 8 characters");
const binanceApiKeySchema = z.string().min(10, "Binance API key is required");
const binanceApiSecretSchema = z.string().min(10, "Binance API secret is required");

export default function Auth() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  // Sign In State
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  // Sign Up State
  const [signUpEmail, setSignUpEmail] = useState("");
  const [signUpPassword, setSignUpPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [location, setLocation] = useState("");
  const [binanceApiKey, setBinanceApiKey] = useState("");
  const [binanceApiSecret, setBinanceApiSecret] = useState("");
  const [idDocument, setIdDocument] = useState<File | null>(null);
  const [dataConsent, setDataConsent] = useState(false);
  const [termsConsent, setTermsConsent] = useState(false);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      // Validate all fields
      emailSchema.parse(signUpEmail);
      passwordSchema.parse(signUpPassword);
      binanceApiKeySchema.parse(binanceApiKey);
      binanceApiSecretSchema.parse(binanceApiSecret);

      if (!fullName.trim()) {
        throw new Error("Full name is required");
      }
      if (!dateOfBirth) {
        throw new Error("Date of birth is required");
      }
      if (!location.trim()) {
        throw new Error("Location is required");
      }
      if (!idDocument) {
        throw new Error("ID verification document is required");
      }
      if (!dataConsent) {
        throw new Error("You must consent to data processing as per ISO 9001 requirements");
      }
      if (!termsConsent) {
        throw new Error("You must accept the terms and conditions");
      }

      // Check if user is at least 18 years old
      const birthDate = new Date(dateOfBirth);
      const today = new Date();
      let age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();
      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      if (age < 18) {
        throw new Error("You must be at least 18 years old to register");
      }
      
      setLoading(true);

      // Step 1: Create user account
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: signUpEmail,
        password: signUpPassword,
        options: {
          emailRedirectTo: `${window.location.origin}/`,
          data: {
            full_name: fullName
          }
        }
      });

      if (authError) throw authError;
      if (!authData.user) throw new Error("Failed to create user account");

      // Step 2: Upload ID document to storage
      const fileExt = idDocument.name.split('.').pop();
      const fileName = `${authData.user.id}/id-verification.${fileExt}`;
      
      const { error: uploadError } = await supabase.storage
        .from('id-verification')
        .upload(fileName, idDocument, {
          cacheControl: '3600',
          upsert: false
        });

      if (uploadError) throw new Error(`ID upload failed: ${uploadError.message}`);

      // Step 3: Update profile with KYC information
      const { error: profileError } = await supabase
        .from('profiles')
        .update({
          full_name: fullName,
          date_of_birth: dateOfBirth,
          location: location,
          id_document_path: fileName,
          data_consent_given: true,
          data_consent_date: new Date().toISOString(),
          kyc_status: 'pending'
        })
        .eq('id', authData.user.id);

      if (profileError) throw new Error(`Profile update failed: ${profileError.message}`);

      // Step 4: Encrypt and store Binance credentials via edge function
      const { error: credentialsError } = await supabase.functions.invoke('store-binance-credentials', {
        body: {
          userId: authData.user.id,
          apiKey: binanceApiKey,
          apiSecret: binanceApiSecret
        }
      });

      if (credentialsError) throw new Error(`Credentials storage failed: ${credentialsError.message}`);

      // Step 5: Log audit trail
      const { error: auditError } = await supabase
        .from('data_access_audit')
        .insert({
          user_id: authData.user.id,
          accessed_by: authData.user.id,
          access_type: 'CREATE',
          resource_type: 'KYC_REGISTRATION',
          metadata: {
            consent_given: true,
            kyc_status: 'pending',
            timestamp: new Date().toISOString()
          }
        });

      if (auditError) console.warn('Audit log failed:', auditError);

      toast.success("Registration complete! Your account is pending KYC verification.");
      
      // Clear form
      setSignUpEmail("");
      setSignUpPassword("");
      setFullName("");
      setDateOfBirth("");
      setLocation("");
      setBinanceApiKey("");
      setBinanceApiSecret("");
      setIdDocument(null);
      setDataConsent(false);
      setTermsConsent(false);
      
    } catch (error) {
      if (error instanceof z.ZodError) {
        toast.error(error.errors[0].message);
      } else if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Failed to create account");
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

      toast.success("Signed in successfully!");
      navigate("/");
    } catch (error) {
      if (error instanceof z.ZodError) {
        toast.error(error.errors[0].message);
      } else if (error instanceof Error) {
        toast.error(error.message);
      } else {
        toast.error("Failed to sign in");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-primary/5 p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">🌈 AUREON Access</CardTitle>
          <CardDescription className="text-center">
            Quantum Trading System Authentication
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="signin" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
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
                  <Input
                    id="signin-password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={loading}
                >
                  {loading ? "Signing in..." : "Sign In"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleSignUp} className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
                <div className="space-y-4">
                  {/* Personal Information */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold mb-3 text-sm">Personal Information</h3>
                    
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="signup-name">Full Name *</Label>
                        <Input
                          id="signup-name"
                          type="text"
                          placeholder="John Doe"
                          value={fullName}
                          onChange={(e) => setFullName(e.target.value)}
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="signup-dob">Date of Birth *</Label>
                        <Input
                          id="signup-dob"
                          type="date"
                          value={dateOfBirth}
                          onChange={(e) => setDateOfBirth(e.target.value)}
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="signup-location">Location *</Label>
                        <Input
                          id="signup-location"
                          type="text"
                          placeholder="City, Country"
                          value={location}
                          onChange={(e) => setLocation(e.target.value)}
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Account Credentials */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold mb-3 text-sm">Account Credentials</h3>
                    
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="signup-email">Email *</Label>
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
                        <Label htmlFor="signup-password">Password *</Label>
                        <Input
                          id="signup-password"
                          type="password"
                          placeholder="Min. 8 characters"
                          value={signUpPassword}
                          onChange={(e) => setSignUpPassword(e.target.value)}
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Binance API Credentials */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold mb-3 text-sm">Binance API Credentials</h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Your personal Binance API credentials are encrypted and stored securely.
                    </p>
                    
                    <div className="space-y-3">
                      <div className="space-y-2">
                        <Label htmlFor="binance-api-key">Binance API Key *</Label>
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
                        <Label htmlFor="binance-api-secret">Binance API Secret *</Label>
                        <Input
                          id="binance-api-secret"
                          type="password"
                          placeholder="Your Binance API Secret"
                          value={binanceApiSecret}
                          onChange={(e) => setBinanceApiSecret(e.target.value)}
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* ID Verification */}
                  <div className="border-b pb-4">
                    <h3 className="font-semibold mb-3 text-sm">ID Verification</h3>
                    <p className="text-xs text-muted-foreground mb-3">
                      Upload a government-issued ID (passport, driver's license, or national ID card).
                      Accepted formats: JPG, PNG, PDF (max 5MB).
                    </p>
                    
                    <div className="space-y-2">
                      <Label htmlFor="id-document">ID Document *</Label>
                      <Input
                        id="id-document"
                        type="file"
                        accept=".jpg,.jpeg,.png,.pdf"
                        onChange={(e) => setIdDocument(e.target.files?.[0] || null)}
                        required
                      />
                      {idDocument && (
                        <p className="text-xs text-muted-foreground">
                          Selected: {idDocument.name} ({(idDocument.size / 1024 / 1024).toFixed(2)} MB)
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Consent & Terms */}
                  <div className="space-y-3">
                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="data-consent"
                        checked={dataConsent}
                        onCheckedChange={(checked) => setDataConsent(checked as boolean)}
                        required
                      />
                      <Label htmlFor="data-consent" className="text-xs leading-tight cursor-pointer">
                        I consent to the processing of my personal data in accordance with ISO 9001 standards. 
                        I understand that my data will be stored securely and used solely for KYC verification 
                        and trading purposes. I have the right to access, modify, or delete my data at any time.
                      </Label>
                    </div>

                    <div className="flex items-start space-x-2">
                      <Checkbox
                        id="terms-consent"
                        checked={termsConsent}
                        onCheckedChange={(checked) => setTermsConsent(checked as boolean)}
                        required
                      />
                      <Label htmlFor="terms-consent" className="text-xs leading-tight cursor-pointer">
                        I accept the Terms and Conditions and Privacy Policy. I confirm that I am at least 
                        18 years old and that all information provided is accurate and truthful.
                      </Label>
                    </div>
                  </div>
                </div>

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={loading}
                >
                  {loading ? "Creating Account..." : "Complete Registration"}
                </Button>

                <p className="text-xs text-center text-muted-foreground">
                  Your account will be reviewed for KYC verification within 24-48 hours.
                </p>
              </form>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
