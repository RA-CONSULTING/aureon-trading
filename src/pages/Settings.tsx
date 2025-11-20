import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { supabase } from "@/integrations/supabase/client";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { Loader2, CheckCircle2, XCircle, Clock, Shield, Key, User } from "lucide-react";

export default function Settings() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [userId, setUserId] = useState<string>("");
  
  // Profile data
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [location, setLocation] = useState("");
  const [kycStatus, setKycStatus] = useState<string>("pending");
  const [kycVerifiedAt, setKycVerifiedAt] = useState<string | null>(null);
  
  // Binance credentials
  const [hasCredentials, setHasCredentials] = useState(false);
  const [credentialsLastUsed, setCredentialsLastUsed] = useState<string | null>(null);
  const [showCredentialsForm, setShowCredentialsForm] = useState(false);
  const [binanceApiKey, setBinanceApiKey] = useState("");
  const [binanceApiSecret, setBinanceApiSecret] = useState("");

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const { data: { user }, error: authError } = await supabase.auth.getUser();
      
      if (authError || !user) {
        navigate("/auth");
        return;
      }

      setUserId(user.id);
      setEmail(user.email || "");

      // Load profile data
      const { data: profile, error: profileError } = await supabase
        .from("profiles")
        .select("*")
        .eq("id", user.id)
        .single();

      if (!profileError && profile) {
        setFullName(profile.full_name || "");
        setDateOfBirth(profile.date_of_birth || "");
        setLocation(profile.location || "");
        setKycStatus(profile.kyc_status || "pending");
        setKycVerifiedAt(profile.kyc_verified_at);
      }

      // Check for Binance credentials
      const { data: credentials, error: credError } = await supabase
        .from("user_binance_credentials")
        .select("last_used_at")
        .eq("user_id", user.id)
        .single();

      if (!credError && credentials) {
        setHasCredentials(true);
        setCredentialsLastUsed(credentials.last_used_at);
      }

    } catch (error) {
      console.error("Error loading user data:", error);
      toast({
        title: "Error",
        description: "Failed to load user settings",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async () => {
    setSaving(true);
    try {
      const { error } = await supabase
        .from("profiles")
        .update({
          full_name: fullName,
          date_of_birth: dateOfBirth,
          location: location,
        })
        .eq("id", userId);

      if (error) throw error;

      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    } catch (error) {
      console.error("Error updating profile:", error);
      toast({
        title: "Error",
        description: "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateCredentials = async () => {
    if (!binanceApiKey.trim() || !binanceApiSecret.trim()) {
      toast({
        title: "Validation Error",
        description: "Please provide both API key and secret",
        variant: "destructive",
      });
      return;
    }

    setSaving(true);
    try {
      const { data, error } = await supabase.functions.invoke('store-binance-credentials', {
        body: {
          userId,
          apiKey: binanceApiKey,
          apiSecret: binanceApiSecret,
        },
      });

      if (error) throw error;

      toast({
        title: "Success",
        description: "Binance credentials updated successfully",
      });
      
      setBinanceApiKey("");
      setBinanceApiSecret("");
      setShowCredentialsForm(false);
      loadUserData(); // Reload to update credential status
    } catch (error) {
      console.error("Error updating credentials:", error);
      toast({
        title: "Error",
        description: "Failed to update Binance credentials",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const getKycStatusBadge = () => {
    switch (kycStatus) {
      case "verified":
        return <Badge className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />Verified</Badge>;
      case "rejected":
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge variant="secondary"><Clock className="w-3 h-3 mr-1" />Pending Review</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your account settings and preferences</p>
      </div>

      <Tabs defaultValue="profile" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="profile">
            <User className="w-4 h-4 mr-2" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="credentials">
            <Key className="w-4 h-4 mr-2" />
            API Credentials
          </TabsTrigger>
          <TabsTrigger value="kyc">
            <Shield className="w-4 h-4 mr-2" />
            KYC Status
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Profile Information</CardTitle>
              <CardDescription>
                Update your personal information and contact details
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  disabled
                  className="bg-muted"
                />
                <p className="text-sm text-muted-foreground">
                  Email cannot be changed here
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter your full name"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="dateOfBirth">Date of Birth</Label>
                <Input
                  id="dateOfBirth"
                  type="date"
                  value={dateOfBirth}
                  onChange={(e) => setDateOfBirth(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="location">Location</Label>
                <Input
                  id="location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="City, Country"
                />
              </div>

              <Separator className="my-4" />

              <Button 
                onClick={handleUpdateProfile} 
                disabled={saving}
                className="w-full sm:w-auto"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  "Save Changes"
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="credentials" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Binance API Credentials</CardTitle>
              <CardDescription>
                Manage your Binance API credentials for trading
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border rounded-lg bg-muted/50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Status</span>
                  {hasCredentials ? (
                    <Badge className="bg-green-500">
                      <CheckCircle2 className="w-3 h-3 mr-1" />
                      Configured
                    </Badge>
                  ) : (
                    <Badge variant="secondary">
                      <XCircle className="w-3 h-3 mr-1" />
                      Not Configured
                    </Badge>
                  )}
                </div>
                {credentialsLastUsed && (
                  <p className="text-sm text-muted-foreground">
                    Last used: {new Date(credentialsLastUsed).toLocaleString()}
                  </p>
                )}
              </div>

              {!showCredentialsForm ? (
                <Button 
                  onClick={() => setShowCredentialsForm(true)}
                  variant={hasCredentials ? "outline" : "default"}
                  className="w-full sm:w-auto"
                >
                  {hasCredentials ? "Update Credentials" : "Add Credentials"}
                </Button>
              ) : (
                <div className="space-y-4 p-4 border rounded-lg">
                  <div className="space-y-2">
                    <Label htmlFor="apiKey">Binance API Key</Label>
                    <Input
                      id="apiKey"
                      type="text"
                      value={binanceApiKey}
                      onChange={(e) => setBinanceApiKey(e.target.value)}
                      placeholder="Enter your Binance API key"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="apiSecret">Binance API Secret</Label>
                    <Input
                      id="apiSecret"
                      type="password"
                      value={binanceApiSecret}
                      onChange={(e) => setBinanceApiSecret(e.target.value)}
                      placeholder="Enter your Binance API secret"
                    />
                  </div>

                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <p className="text-sm text-yellow-700 dark:text-yellow-400">
                      ⚠️ Your credentials are encrypted using AES-256-GCM encryption before storage.
                      Never share your API secret with anyone.
                    </p>
                  </div>

                  <div className="flex gap-2">
                    <Button 
                      onClick={handleUpdateCredentials}
                      disabled={saving}
                    >
                      {saving ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        "Save Credentials"
                      )}
                    </Button>
                    <Button 
                      variant="outline"
                      onClick={() => {
                        setShowCredentialsForm(false);
                        setBinanceApiKey("");
                        setBinanceApiSecret("");
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="kyc" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>KYC Verification Status</CardTitle>
              <CardDescription>
                View your Know Your Customer (KYC) verification status
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 border rounded-lg bg-muted/50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium">Verification Status</span>
                  {getKycStatusBadge()}
                </div>
                
                {kycStatus === "verified" && kycVerifiedAt && (
                  <p className="text-sm text-muted-foreground">
                    Verified on: {new Date(kycVerifiedAt).toLocaleDateString()}
                  </p>
                )}

                {kycStatus === "pending" && (
                  <p className="text-sm text-muted-foreground mt-2">
                    Your KYC application is under review. You will be notified once it's processed.
                  </p>
                )}

                {kycStatus === "rejected" && (
                  <div className="mt-2 p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                    <p className="text-sm text-red-700 dark:text-red-400">
                      Your KYC application was rejected. Please contact support for more information.
                    </p>
                  </div>
                )}
              </div>

              <div className="p-4 border rounded-lg">
                <h3 className="font-medium mb-2">Submitted Information</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Full Name:</span>
                    <span className="font-medium">{fullName || "Not provided"}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Date of Birth:</span>
                    <span className="font-medium">
                      {dateOfBirth ? new Date(dateOfBirth).toLocaleDateString() : "Not provided"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Location:</span>
                    <span className="font-medium">{location || "Not provided"}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
