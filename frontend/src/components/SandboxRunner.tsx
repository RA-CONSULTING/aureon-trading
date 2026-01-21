import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

type Metric = {
  iso_time: string;
  unix_time: number;
  mono_ns: number;
  coherence_index: number;
  schumann_lock: number;
  prime_10_9_1_balance: number;
  lattice_id_match: number;
  resonance_gain_db: number;
  probability_uplift_proxy: number;
  safety_status: "OK" | "THROTTLED" | "MUTED";
  event_marker?: string;
};

class CsvSink {
  private headerWritten = false;
  private lines: string[] = [];
  constructor(private filename = "auris_metrics.csv") {}
  
  write(row: Metric) {
    if (!this.headerWritten) {
      this.lines.push(Object.keys(row).join(","));
      this.headerWritten = true;
    }
    const vals = Object.values(row).map(v =>
      typeof v === "number" ? v.toString() : (v ?? "").toString()
    );
    this.lines.push(vals.join(","));
  }
  
  download() {
    const blob = new Blob([this.lines.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = this.filename;
    a.click();
    URL.revokeObjectURL(url);
  }
}

const SandboxRunner: React.FC = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [currentMetric, setCurrentMetric] = useState<Metric | null>(null);
  const [timeRemaining, setTimeRemaining] = useState(1200); // 20 minutes
  const [progress, setProgress] = useState(0);
  const csvSinkRef = useRef<CsvSink>(new CsvSink("field_pull_metrics.csv"));
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
  const db = (lin: number) => 20 * Math.log10(Math.max(1e-9, lin));
  const hiResNs = () => Math.round(performance.now() * 1e6);

  const uplift = (coh: number, lock: number, bal: number): number => {
    const base = clamp01(0.6 * coh + 0.3 * lock + 0.1 * bal);
    return Math.min(100, Math.pow(base, 1.5) * 100);
  };

  const sealMatch = (name: string, dob: string): number => {
    const s = `${name}|${dob}|10-9-1`;
    let h = 0;
    for (let i = 0; i < s.length; i++) h = (h * 131 + s.charCodeAt(i)) >>> 0;
    return 0.7 + ((h % 3000) / 10000);
  };

  const generateMetric = (): Metric => {
    const now = new Date();
    const t = performance.now() / 1000;
    
    // Simulate field measurements with realistic variations
    const coherence = clamp01(0.8 + 0.15 * Math.sin(t * 0.1) + 0.05 * Math.random());
    const lock = clamp01(0.75 + 0.2 * Math.cos(t * 0.07) + 0.05 * Math.random());
    const balance = clamp01(Math.abs(Math.sin(t * 0.05)) + 0.1 * Math.random());
    const idMatch = sealMatch("Gary Leckey", "1991-11-02");
    const gain = 1.0 + 0.5 * Math.sin(t * 0.03);
    
    return {
      iso_time: now.toISOString(),
      unix_time: Math.floor(now.getTime() / 1000),
      mono_ns: hiResNs(),
      coherence_index: coherence,
      schumann_lock: lock,
      prime_10_9_1_balance: balance,
      lattice_id_match: idMatch,
      resonance_gain_db: db(gain),
      probability_uplift_proxy: uplift(coherence, lock, balance),
      safety_status: coherence > 0.95 ? "THROTTLED" : "OK"
    };
  };

  const startExperiment = () => {
    setIsRunning(true);
    setTimeRemaining(1200);
    setProgress(0);
    csvSinkRef.current = new CsvSink("field_pull_metrics.csv");

    intervalRef.current = setInterval(() => {
      const metric = generateMetric();
      setCurrentMetric(metric);
      csvSinkRef.current.write(metric);
      
      setTimeRemaining(prev => {
        const newTime = Math.max(0, prev - 1);
        setProgress(((1200 - newTime) / 1200) * 100);
        if (newTime === 0) {
          stopExperiment();
        }
        return newTime;
      });
    }, 1000);
  };

  const stopExperiment = () => {
    setIsRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const downloadData = () => {
    csvSinkRef.current.download();
  };

  return (
    <div className="space-y-6">
      <Card className="bg-black/50 border-green-500">
        <CardHeader>
          <CardTitle className="text-green-400 text-center text-2xl">
            🧪 Field Pull Sandbox Runner
          </CardTitle>
          <div className="text-center text-green-300 text-sm">
            21:20–21:40 UK Time • Schumann + 10-9-1 Seal • Live Metrics
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex justify-center gap-4">
            <Button
              onClick={isRunning ? stopExperiment : startExperiment}
              className={`${isRunning ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}`}
            >
              {isRunning ? 'Stop Experiment' : 'Start 20min Experiment'}
            </Button>
            <Button onClick={downloadData} variant="outline" className="border-blue-500 text-blue-400">
              Download CSV
            </Button>
          </div>

          {isRunning && (
            <div className="space-y-4">
              <div className="text-center">
                <div className="text-lg text-white mb-2">
                  Time Remaining: {Math.floor(timeRemaining / 60)}:{(timeRemaining % 60).toString().padStart(2, '0')}
                </div>
                <Progress value={progress} className="w-full" />
              </div>

              {currentMetric && (
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="bg-gray-900 border-purple-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-purple-400">Coherence</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-mono text-purple-300">
                        {currentMetric.coherence_index.toFixed(3)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gray-900 border-cyan-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-cyan-400">Schumann Lock</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-mono text-cyan-300">
                        {currentMetric.schumann_lock.toFixed(3)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gray-900 border-amber-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-amber-400">10-9-1 Balance</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-mono text-amber-300">
                        {currentMetric.prime_10_9_1_balance.toFixed(3)}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-gray-900 border-green-500">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm text-green-400">Uplift Proxy</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-mono text-green-300">
                        {currentMetric.probability_uplift_proxy.toFixed(1)}%
                      </div>
                    </CardContent>
                  </Card>
                </div>
              )}

              <div className="text-center">
                <Badge variant={currentMetric?.safety_status === "OK" ? "default" : "destructive"}>
                  Safety: {currentMetric?.safety_status || "UNKNOWN"}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SandboxRunner;