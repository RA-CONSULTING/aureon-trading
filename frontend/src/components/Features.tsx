import { Card, CardContent } from "@/components/ui/card";
import { LineChart, Wallet, BarChart3, Globe, Lock, Users } from "lucide-react";

const features = [
  {
    icon: LineChart,
    title: "Advanced Charting",
    description: "Professional-grade charts with 100+ technical indicators and drawing tools",
  },
  {
    icon: Wallet,
    title: "Multi-Asset Trading",
    description: "Trade forex, crypto, stocks, commodities, and indices from one platform",
  },
  {
    icon: BarChart3,
    title: "Portfolio Analytics",
    description: "Track performance, risk metrics, and optimize your trading strategy",
  },
  {
    icon: Globe,
    title: "Global Markets",
    description: "Access markets worldwide 24/7 with competitive spreads and execution",
  },
  {
    icon: Lock,
    title: "Bank-Level Security",
    description: "Your funds and data protected with enterprise-grade encryption",
  },
  {
    icon: Users,
    title: "Expert Support",
    description: "24/7 customer support and educational resources for all skill levels",
  },
];

const Features = () => {
  return (
    <section className="py-24 bg-gradient-to-b from-background to-card/20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Everything You Need to Trade</h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Professional tools and features designed to give you the edge in financial markets
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Card key={feature.title} className="bg-card border-border hover:border-primary/50 transition-all duration-300">
                <CardContent className="p-6">
                  <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                    <Icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
};

export default Features;
