import Navbar from "@/components/Navbar";
import { ExchangeCredentialsManager } from "@/components/ExchangeCredentialsManager";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const Settings = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">⚙️</span>
            <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          </div>
          
          <Card className="bg-card border-border">
            <CardContent className="pt-6">
              <Tabs defaultValue="trading" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="trading">Trading</TabsTrigger>
                  <TabsTrigger value="credentials">API Credentials</TabsTrigger>
                  <TabsTrigger value="alerts">Alerts</TabsTrigger>
                </TabsList>
                
                <TabsContent value="trading" className="mt-6">
                  <ExchangeCredentialsManager />
                </TabsContent>
                
                <TabsContent value="credentials" className="mt-6">
                  <ExchangeCredentialsManager />
                </TabsContent>
                
                <TabsContent value="alerts" className="mt-6">
                  <div className="text-muted-foreground text-center py-8">
                    Alert settings coming soon...
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Settings;
