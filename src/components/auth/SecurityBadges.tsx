import { Shield, Lock, Globe } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const badges = [
  {
    icon: Lock,
    label: "AES-256",
    tooltip: "Your API keys are encrypted with AES-256-GCM, the same standard used by banks and governments."
  },
  {
    icon: Shield,
    label: "RLS Protected",
    tooltip: "Row Level Security ensures only you can access your own data. Even our systems can't see your credentials."
  },
  {
    icon: Globe,
    label: "TLS 1.3",
    tooltip: "All data transmitted over HTTPS with TLS 1.3 encryption. Your credentials never travel unprotected."
  }
];

export function SecurityBadges() {
  return (
    <TooltipProvider>
      <div className="flex items-center justify-center gap-3 py-3 border-t border-border/30 mt-4">
        {badges.map((badge) => (
          <Tooltip key={badge.label}>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-muted/50 text-muted-foreground hover:text-foreground transition-colors cursor-help">
                <badge.icon className="h-3 w-3" />
                <span className="text-xs font-medium">{badge.label}</span>
              </div>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-[200px] text-center">
              <p className="text-xs">{badge.tooltip}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </div>
    </TooltipProvider>
  );
}
