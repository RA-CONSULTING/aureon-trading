import { useBrainState, type BrainState, type WisdomConsensus } from "@/hooks/useBrainState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Brain, 
  AlertTriangle, 
  CheckCircle2, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Eye,
  Target,
  Sparkles,
  Globe,
  BarChart3,
  Lightbulb
} from "lucide-react";
import { format } from "date-fns";

// Fear & Greed color coding
function getFearGreedColor(value: number): string {
  if (value <= 25) return "text-red-500";
  if (value <= 45) return "text-orange-500";
  if (value <= 55) return "text-yellow-500";
  if (value <= 75) return "text-green-400";
  return "text-green-500";
}

function getFearGreedBg(value: number): string {
  if (value <= 25) return "bg-red-500/20";
  if (value <= 45) return "bg-orange-500/20";
  if (value <= 55) return "bg-yellow-500/20";
  if (value <= 75) return "bg-green-400/20";
  return "bg-green-500/20";
}

// Direction icon
function DirectionIcon({ direction }: { direction: string }) {
  if (direction === "BULLISH") return <TrendingUp className="w-4 h-4 text-green-500" />;
  if (direction === "BEARISH") return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Minus className="w-4 h-4 text-muted-foreground" />;
}

// Wisdom consensus display
function WisdomConsensusDisplay({ wisdom }: { wisdom: WisdomConsensus }) {
  if (!wisdom || Object.keys(wisdom).length === 0) {
    return <span className="text-muted-foreground text-xs">Awaiting wisdom council...</span>;
  }

  const civilizations = wisdom.civilization_actions || {};
  const civIcons: Record<string, string> = {
    celtic: "☘️",
    aztec: "🦅",
    vedic: "🕉️",
    egyptian: "🔺",
    greek: "🏛️",
    chinese: "☯️",
    mayan: "🌀",
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Badge variant={wisdom.sentiment === "BULLISH" ? "default" : wisdom.sentiment === "BEARISH" ? "destructive" : "secondary"}>
          {wisdom.sentiment || "NEUTRAL"}
        </Badge>
        <span className="text-sm text-muted-foreground">
          {wisdom.confidence ? `${(wisdom.confidence * 100).toFixed(0)}% confidence` : ""}
        </span>
      </div>
      {(wisdom.bullish_votes !== undefined || wisdom.bearish_votes !== undefined) && (
        <div className="flex gap-2 text-xs">
          <span className="text-green-500">📈 {wisdom.bullish_votes || 0}</span>
          <span className="text-red-500">📉 {wisdom.bearish_votes || 0}</span>
          <span className="text-muted-foreground">⚖️ {wisdom.neutral_votes || 0}</span>
        </div>
      )}
      {Object.keys(civilizations).length > 0 && (
        <div className="flex flex-wrap gap-1">
          {Object.entries(civilizations).map(([civ, action]) => (
            <span key={civ} className="text-xs px-1.5 py-0.5 rounded bg-muted" title={`${civ}: ${action}`}>
              {civIcons[civ.toLowerCase()] || "🌍"} {String(action).slice(0, 8)}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export function BrainStatePanel() {
  const { brainState, loading, lastUpdated } = useBrainState(true, 10000);

  if (loading && !brainState.id) {
    return (
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary animate-pulse" />
            AUREON Brain
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">Awaiting cognitive state from Python terminal...</p>
        </CardContent>
      </Card>
    );
  }

  const {
    fear_greed,
    fear_greed_class,
    btc_price,
    btc_change_24h,
    manipulation_probability,
    red_flags,
    green_flags,
    council_consensus,
    council_action,
    truth_score,
    spoof_score,
    brain_directive,
    prediction_direction,
    prediction_confidence,
    overall_accuracy,
    total_predictions,
    speculations,
    wisdom_consensus,
    timestamp,
  } = brainState;

  const manipulationPct = Math.round(manipulation_probability * 100);
  const truthPct = Math.round(truth_score * 100);
  const spoofPct = Math.round(spoof_score * 100);
  const accuracyPct = Math.round(overall_accuracy * 100);
  const predConfPct = Math.round(prediction_confidence * 100);

  return (
    <Card className="md:col-span-2 border-primary/30 bg-gradient-to-br from-background to-primary/5">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-primary" />
            AUREON Brain - Live Cognitive State
          </CardTitle>
          {lastUpdated && (
            <span className="text-xs text-muted-foreground">
              Updated {format(lastUpdated, "HH:mm:ss")}
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Row 1: Fear & Greed + Market */}
        <div className="grid grid-cols-2 gap-4">
          <div className={`p-3 rounded-lg ${getFearGreedBg(fear_greed)}`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-muted-foreground">Fear & Greed</span>
              <Eye className="w-4 h-4 text-muted-foreground" />
            </div>
            <div className={`text-3xl font-bold ${getFearGreedColor(fear_greed)}`}>{fear_greed}</div>
            <div className="text-sm text-muted-foreground">{fear_greed_class}</div>
            <Progress value={fear_greed} className="mt-2 h-1.5" />
          </div>

          <div className="p-3 rounded-lg bg-muted/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-muted-foreground">BTC Price</span>
              <DirectionIcon direction={btc_change_24h >= 0 ? "BULLISH" : "BEARISH"} />
            </div>
            <div className="text-2xl font-bold font-mono">
              ${btc_price.toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
            <div className={`text-sm ${btc_change_24h >= 0 ? "text-green-500" : "text-red-500"}`}>
              {btc_change_24h >= 0 ? "+" : ""}{btc_change_24h.toFixed(2)}%
            </div>
          </div>
        </div>

        {/* Row 2: Manipulation Detection */}
        <div className="p-3 rounded-lg bg-muted/30">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <AlertTriangle className={`w-4 h-4 ${manipulationPct > 50 ? "text-red-500" : "text-green-500"}`} />
              <span className="text-sm font-medium">Manipulation Detection</span>
            </div>
            <Badge variant={manipulationPct > 50 ? "destructive" : "secondary"}>
              {manipulationPct}%
            </Badge>
          </div>
          <Progress value={manipulationPct} className="h-2 mb-2" />
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              {green_flags.length > 0 ? (
                <div className="space-y-1">
                  {green_flags.slice(0, 2).map((flag, i) => (
                    <div key={i} className="flex items-center gap-1 text-green-500">
                      <CheckCircle2 className="w-3 h-3" />
                      <span className="truncate">{flag}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-muted-foreground">No green flags</span>
              )}
            </div>
            <div>
              {red_flags.length > 0 ? (
                <div className="space-y-1">
                  {red_flags.slice(0, 2).map((flag, i) => (
                    <div key={i} className="flex items-center gap-1 text-red-500">
                      <AlertTriangle className="w-3 h-3" />
                      <span className="truncate">{flag}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="text-muted-foreground">No red flags</span>
              )}
            </div>
          </div>
        </div>

        {/* Row 3: Truth Council */}
        <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">Truth Council</span>
          </div>
          <div className="flex items-center justify-between mb-2">
            <Badge variant="outline" className="font-mono text-xs">
              {council_consensus}
            </Badge>
            <span className="text-xs text-muted-foreground">→ {council_action}</span>
          </div>
          <div className="flex gap-4 text-xs">
            <div>
              <span className="text-muted-foreground">Truth: </span>
              <span className="text-green-500 font-medium">{truthPct}%</span>
            </div>
            <div>
              <span className="text-muted-foreground">Spoof: </span>
              <span className="text-red-500 font-medium">{spoofPct}%</span>
            </div>
          </div>
        </div>

        {/* Row 4: Prediction + Accuracy */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-muted/30">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">Prediction</span>
            </div>
            <div className="flex items-center gap-2">
              <DirectionIcon direction={prediction_direction} />
              <span className={`font-bold ${
                prediction_direction === "BULLISH" ? "text-green-500" : 
                prediction_direction === "BEARISH" ? "text-red-500" : "text-muted-foreground"
              }`}>
                {prediction_direction}
              </span>
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              {predConfPct}% confidence
            </div>
          </div>

          <div className="p-3 rounded-lg bg-muted/30">
            <div className="flex items-center gap-2 mb-2">
              <BarChart3 className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">Brain Accuracy</span>
            </div>
            <div className="text-2xl font-bold">{accuracyPct}%</div>
            <div className="text-xs text-muted-foreground">
              {total_predictions} predictions
            </div>
          </div>
        </div>

        {/* Row 5: Wisdom Consensus */}
        <div className="p-3 rounded-lg bg-muted/30">
          <div className="flex items-center gap-2 mb-2">
            <Globe className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium">7 Civilization Wisdom</span>
          </div>
          <WisdomConsensusDisplay wisdom={wisdom_consensus} />
        </div>

        {/* Row 6: Brain Directive */}
        {brain_directive && (
          <div className="p-3 rounded-lg bg-gradient-to-r from-primary/10 to-primary/5 border border-primary/30">
            <div className="flex items-center gap-2 mb-1">
              <Brain className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-primary">Brain Directive</span>
            </div>
            <p className="text-sm">{brain_directive}</p>
          </div>
        )}

        {/* Row 7: Speculations (if any) */}
        {speculations.length > 0 && (
          <div className="p-3 rounded-lg bg-muted/20">
            <div className="flex items-center gap-2 mb-2">
              <Lightbulb className="w-4 h-4 text-yellow-500" />
              <span className="text-sm font-medium">Speculative Insights</span>
            </div>
            <ul className="space-y-1 text-xs text-muted-foreground">
              {speculations.slice(0, 3).map((spec, i) => (
                <li key={i} className="flex items-start gap-1">
                  <span className="text-yellow-500">💭</span>
                  <span>{spec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
