import { Card } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { useQGITAConfig } from '@/hooks/useQGITAConfig';
import { Settings, RotateCcw } from 'lucide-react';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { useState } from 'react';

export function QGITAConfigPanel() {
  const { config, updateConfig, resetToDefaults } = useQGITAConfig();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card className="p-4">
      <Collapsible open={isOpen} onOpenChange={setIsOpen}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Settings className="w-4 h-4 text-primary" />
            <h3 className="font-semibold">QGITA Configuration</h3>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={resetToDefaults}
              className="h-8 text-xs"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Reset
            </Button>
            <CollapsibleTrigger asChild>
              <Button variant="outline" size="sm" className="h-8">
                {isOpen ? 'Hide' : 'Show'}
              </Button>
            </CollapsibleTrigger>
          </div>
        </div>

        <CollapsibleContent className="space-y-6">
          {/* Detection Sensitivity */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-primary">Detection Sensitivity</h4>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Curvature Threshold Percentile</Label>
                <span className="text-xs text-muted-foreground">{config.curvatureThresholdPercentile}%</span>
              </div>
              <Slider
                value={[config.curvatureThresholdPercentile]}
                onValueChange={([value]) => updateConfig({ curvatureThresholdPercentile: value })}
                min={80}
                max={99}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">Higher = fewer, stronger signals</p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Golden Ratio Tolerance</Label>
                <span className="text-xs text-muted-foreground">{config.goldenRatioTolerance.toFixed(3)}</span>
              </div>
              <Slider
                value={[config.goldenRatioTolerance * 100]}
                onValueChange={([value]) => updateConfig({ goldenRatioTolerance: value / 100 })}
                min={1}
                max={10}
                step={0.5}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">Lower = stricter φ alignment</p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Lighthouse Threshold (σ)</Label>
                <span className="text-xs text-muted-foreground">{config.lighthouseThresholdSigma.toFixed(1)}</span>
              </div>
              <Slider
                value={[config.lighthouseThresholdSigma * 10]}
                onValueChange={([value]) => updateConfig({ lighthouseThresholdSigma: value / 10 })}
                min={15}
                max={30}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">Higher = fewer LHE events</p>
            </div>
          </div>

          {/* Confidence Thresholds */}
          <div className="space-y-4 pt-4 border-t">
            <h4 className="text-sm font-semibold text-primary">Confidence Thresholds</h4>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Min Confidence for Signal</Label>
                <span className="text-xs text-muted-foreground">{config.minConfidenceForSignal}%</span>
              </div>
              <Slider
                value={[config.minConfidenceForSignal]}
                onValueChange={([value]) => updateConfig({ minConfidenceForSignal: value })}
                min={40}
                max={80}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Tier 1 Threshold (Full Position)</Label>
                <span className="text-xs text-muted-foreground">{config.tier1Threshold}%</span>
              </div>
              <Slider
                value={[config.tier1Threshold]}
                onValueChange={([value]) => updateConfig({ tier1Threshold: value })}
                min={70}
                max={95}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Tier 2 Threshold (Half Position)</Label>
                <span className="text-xs text-muted-foreground">{config.tier2Threshold}%</span>
              </div>
              <Slider
                value={[config.tier2Threshold]}
                onValueChange={([value]) => updateConfig({ tier2Threshold: value })}
                min={50}
                max={75}
                step={5}
                className="w-full"
              />
            </div>
          </div>

          {/* Position Size Multipliers */}
          <div className="space-y-4 pt-4 border-t">
            <h4 className="text-sm font-semibold text-primary">Position Size Multipliers</h4>
            
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Tier 1 Multiplier</Label>
                <span className="text-xs text-muted-foreground">{(config.tier1PositionMultiplier * 100).toFixed(0)}%</span>
              </div>
              <Slider
                value={[config.tier1PositionMultiplier * 100]}
                onValueChange={([value]) => updateConfig({ tier1PositionMultiplier: value / 100 })}
                min={50}
                max={100}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Tier 2 Multiplier</Label>
                <span className="text-xs text-muted-foreground">{(config.tier2PositionMultiplier * 100).toFixed(0)}%</span>
              </div>
              <Slider
                value={[config.tier2PositionMultiplier * 100]}
                onValueChange={([value]) => updateConfig({ tier2PositionMultiplier: value / 100 })}
                min={25}
                max={60}
                step={5}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label className="text-xs">Tier 3 Multiplier</Label>
                <span className="text-xs text-muted-foreground">{(config.tier3PositionMultiplier * 100).toFixed(0)}%</span>
              </div>
              <Slider
                value={[config.tier3PositionMultiplier * 100]}
                onValueChange={([value]) => updateConfig({ tier3PositionMultiplier: value / 100 })}
                min={0}
                max={30}
                step={5}
                className="w-full"
              />
            </div>
          </div>

          {/* Lighthouse Metric Weights */}
          <div className="space-y-4 pt-4 border-t">
            <h4 className="text-sm font-semibold text-primary">Lighthouse Weights</h4>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-xs">Linear Coherence</Label>
                <Slider
                  value={[config.linearCoherenceWeight * 10]}
                  onValueChange={([value]) => updateConfig({ linearCoherenceWeight: value / 10 })}
                  min={0}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <span className="text-xs text-muted-foreground">{config.linearCoherenceWeight.toFixed(1)}</span>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Nonlinear Coherence</Label>
                <Slider
                  value={[config.nonlinearCoherenceWeight * 10]}
                  onValueChange={([value]) => updateConfig({ nonlinearCoherenceWeight: value / 10 })}
                  min={0}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <span className="text-xs text-muted-foreground">{config.nonlinearCoherenceWeight.toFixed(1)}</span>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Cross-Scale φ</Label>
                <Slider
                  value={[config.crossScaleWeight * 10]}
                  onValueChange={([value]) => updateConfig({ crossScaleWeight: value / 10 })}
                  min={0}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <span className="text-xs text-muted-foreground">{config.crossScaleWeight.toFixed(1)}</span>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">G_eff</Label>
                <Slider
                  value={[config.geffWeight * 10]}
                  onValueChange={([value]) => updateConfig({ geffWeight: value / 10 })}
                  min={0}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <span className="text-xs text-muted-foreground">{config.geffWeight.toFixed(1)}</span>
              </div>

              <div className="space-y-2">
                <Label className="text-xs">Anomaly Q</Label>
                <Slider
                  value={[config.anomalyWeight * 10]}
                  onValueChange={([value]) => updateConfig({ anomalyWeight: value / 10 })}
                  min={0}
                  max={20}
                  step={1}
                  className="w-full"
                />
                <span className="text-xs text-muted-foreground">{config.anomalyWeight.toFixed(1)}</span>
              </div>
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </Card>
  );
}
