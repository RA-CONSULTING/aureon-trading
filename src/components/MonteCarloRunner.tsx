import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { MonteCarloEngine, type MonteCarloConfig, type MonteCarloResults, type RandomizationMethod } from '@/core/monteCarloEngine';
import type { BacktestConfig } from '@/core/backtestEngine';
import { Sparkles, Loader2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface MonteCarloRunnerProps {
  baseConfig: BacktestConfig;
  onResultsReady: (results: MonteCarloResults) => void;
}

export const MonteCarloRunner = ({ baseConfig, onResultsReady }: MonteCarloRunnerProps) => {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentSim, setCurrentSim] = useState(0);
  const { toast } = useToast();

  const [config, setConfig] = useState<Omit<MonteCarloConfig, 'baseConfig'>>({
    numSimulations: 100,
    randomizationMethod: 'combined',
    parameterRanges: {
      positionSize: [0.8, 1.0],
      stopLoss: [1.5, 3.0],
      takeProfit: [4.0, 6.0],
      minCoherence: [0.92, 0.96],
      minLighthouseConfidence: [0.65, 0.80],
    },
    bootstrapBlockSize: 20,
    noiseLevel: 0.01,
  });

  const runMonteCarlo = async () => {
    setIsRunning(true);
    setProgress(0);
    setCurrentSim(0);

    try {
      toast({
        title: '🎲 Starting Monte Carlo Simulation',
        description: `Running ${config.numSimulations} randomized scenarios...`,
      });

      // Fetch historical data
      const { data: histData, error: histError } = await supabase.functions.invoke('fetch-historical-data', {
        body: {
          symbol: baseConfig.symbol,
          interval: '15m',
          startTime: baseConfig.startDate.getTime(),
          endTime: baseConfig.endDate.getTime(),
          limit: 1000,
        },
      });

      if (histError) throw histError;
      if (!histData?.candles || histData.candles.length === 0) {
        throw new Error('No historical data available');
      }

      // Run Monte Carlo simulation
      const engine = new MonteCarloEngine();
      const mcConfig: MonteCarloConfig = {
        baseConfig,
        ...config,
      };

      const results = await engine.runSimulation(
        histData.candles,
        mcConfig,
        (prog, sim) => {
          setProgress(prog);
          setCurrentSim(sim);
        }
      );

      // Save results to database
      const { error: saveError } = await supabase
        .from('monte_carlo_simulations')
        .insert({
          symbol: baseConfig.symbol,
          start_date: baseConfig.startDate.toISOString(),
          end_date: baseConfig.endDate.toISOString(),
          num_simulations: config.numSimulations,
          base_config: baseConfig as any,
          randomization_method: config.randomizationMethod,
          results: {
            successRate: results.successRate,
            robustnessScore: results.robustnessScore,
          } as any,
          confidence_intervals: results.aggregateMetrics as any,
          distribution_stats: results.distribution as any,
        });

      if (saveError) throw saveError;

      toast({
        title: '✅ Monte Carlo Complete',
        description: `${results.successRate.toFixed(1)}% success rate | Robustness: ${results.robustnessScore.toFixed(0)}/100`,
        duration: 5000,
      });

      onResultsReady(results);
    } catch (error) {
      console.error('Monte Carlo error:', error);
      toast({
        title: 'Simulation Failed',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setIsRunning(false);
      setProgress(0);
      setCurrentSim(0);
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">🎲 Monte Carlo Simulation</h2>
          <p className="text-sm text-muted-foreground">Test strategy robustness with randomized scenarios</p>
        </div>
        <Button onClick={runMonteCarlo} disabled={isRunning} size="lg">
          {isRunning ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Sim {currentSim}/{config.numSimulations}
            </>
          ) : (
            <>
              <Sparkles className="mr-2 h-5 w-5" />
              Run Simulation
            </>
          )}
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Simulation Settings */}
        <div className="space-y-4">
          <h3 className="font-semibold text-lg">Simulation Settings</h3>
          
          <div>
            <Label>Number of Simulations: {config.numSimulations}</Label>
            <Slider
              value={[config.numSimulations]}
              onValueChange={([value]) => setConfig({ ...config, numSimulations: value })}
              min={10}
              max={500}
              step={10}
              disabled={isRunning}
            />
            <p className="text-xs text-muted-foreground mt-1">More simulations = better confidence intervals</p>
          </div>

          <div>
            <Label>Randomization Method</Label>
            <Select
              value={config.randomizationMethod}
              onValueChange={(value: RandomizationMethod) => setConfig({ ...config, randomizationMethod: value })}
              disabled={isRunning}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="bootstrap">Bootstrap Resampling</SelectItem>
                <SelectItem value="parameter_variation">Parameter Variation</SelectItem>
                <SelectItem value="noise_injection">Noise Injection</SelectItem>
                <SelectItem value="combined">Combined (Recommended)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {(config.randomizationMethod === 'bootstrap' || config.randomizationMethod === 'combined') && (
            <div>
              <Label>Bootstrap Block Size: {config.bootstrapBlockSize}</Label>
              <Slider
                value={[config.bootstrapBlockSize || 20]}
                onValueChange={([value]) => setConfig({ ...config, bootstrapBlockSize: value })}
                min={5}
                max={50}
                step={5}
                disabled={isRunning}
              />
            </div>
          )}

          {(config.randomizationMethod === 'noise_injection' || config.randomizationMethod === 'combined') && (
            <div>
              <Label>Noise Level: {((config.noiseLevel || 0.01) * 100).toFixed(1)}%</Label>
              <Slider
                value={[(config.noiseLevel || 0.01) * 100]}
                onValueChange={([value]) => setConfig({ ...config, noiseLevel: value / 100 })}
                min={0.1}
                max={5}
                step={0.1}
                disabled={isRunning}
              />
            </div>
          )}
        </div>

        {/* Parameter Ranges */}
        {(config.randomizationMethod === 'parameter_variation' || config.randomizationMethod === 'combined') && (
          <div className="space-y-4">
            <h3 className="font-semibold text-lg">Parameter Ranges</h3>
            
            <div>
              <Label>Position Size Range: {(config.parameterRanges?.positionSize?.[0] || 0.8) * 100}% - {(config.parameterRanges?.positionSize?.[1] || 1.0) * 100}%</Label>
              <div className="flex gap-2">
                <Slider
                  value={[
                    (config.parameterRanges?.positionSize?.[0] || 0.8) * 100,
                    (config.parameterRanges?.positionSize?.[1] || 1.0) * 100
                  ]}
                  onValueChange={([min, max]) => setConfig({
                    ...config,
                    parameterRanges: {
                      ...config.parameterRanges!,
                      positionSize: [min / 100, max / 100]
                    }
                  })}
                  min={50}
                  max={100}
                  step={5}
                  disabled={isRunning}
                />
              </div>
            </div>

            <div>
              <Label>Stop Loss Range: {config.parameterRanges?.stopLoss?.[0] || 1.5}% - {config.parameterRanges?.stopLoss?.[1] || 3.0}%</Label>
              <Slider
                value={[
                  config.parameterRanges?.stopLoss?.[0] || 1.5,
                  config.parameterRanges?.stopLoss?.[1] || 3.0
                ]}
                onValueChange={([min, max]) => setConfig({
                  ...config,
                  parameterRanges: {
                    ...config.parameterRanges!,
                    stopLoss: [min, max]
                  }
                })}
                min={0.5}
                max={10}
                step={0.5}
                disabled={isRunning}
              />
            </div>

            <div>
              <Label>Take Profit Range: {config.parameterRanges?.takeProfit?.[0] || 4.0}% - {config.parameterRanges?.takeProfit?.[1] || 6.0}%</Label>
              <Slider
                value={[
                  config.parameterRanges?.takeProfit?.[0] || 4.0,
                  config.parameterRanges?.takeProfit?.[1] || 6.0
                ]}
                onValueChange={([min, max]) => setConfig({
                  ...config,
                  parameterRanges: {
                    ...config.parameterRanges!,
                    takeProfit: [min, max]
                  }
                })}
                min={1}
                max={20}
                step={0.5}
                disabled={isRunning}
              />
            </div>

            <div>
              <Label>Min Coherence Range: {config.parameterRanges?.minCoherence?.[0] || 0.92} - {config.parameterRanges?.minCoherence?.[1] || 0.96}</Label>
              <Slider
                value={[
                  (config.parameterRanges?.minCoherence?.[0] || 0.92) * 1000,
                  (config.parameterRanges?.minCoherence?.[1] || 0.96) * 1000
                ]}
                onValueChange={([min, max]) => setConfig({
                  ...config,
                  parameterRanges: {
                    ...config.parameterRanges!,
                    minCoherence: [min / 1000, max / 1000]
                  }
                })}
                min={850}
                max={980}
                step={5}
                disabled={isRunning}
              />
            </div>
          </div>
        )}
      </div>

      {isRunning && (
        <div className="mt-6 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span className="font-medium">{progress.toFixed(0)}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}
    </Card>
  );
};
