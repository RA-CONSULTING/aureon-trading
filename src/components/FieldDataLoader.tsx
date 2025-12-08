import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, Download } from 'lucide-react';
import { useEcosystemData } from '@/hooks/useEcosystemData';

interface FieldMetric {
  time: number;
  entropy: number;
  coherence: number;
  schumannLock?: number;
  probabilityUplift?: number;
}

interface FieldDataLoaderProps {
  onDataLoaded: (data: FieldMetric[]) => void;
  className?: string;
}

export function FieldDataLoader({ onDataLoaded, className }: FieldDataLoaderProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [dataInfo, setDataInfo] = useState<{ count: number; source: string } | null>(null);
  
  const { metrics, isInitialized } = useEcosystemData();

  const parseCSV = (csvText: string): FieldMetric[] => {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    return lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const row: any = {};
      
      headers.forEach((header, index) => {
        const value = values[index];
        if (!isNaN(Number(value))) {
          row[header] = Number(value);
        } else {
          row[header] = value;
        }
      });
      
      return {
        time: row.time || row.timestamp || 0,
        entropy: row.entropy || 0.5,
        coherence: row.coherence || 0.5,
        schumannLock: row.schumannLock || row.schumann_lock,
        probabilityUplift: row.probabilityUplift || row.probability_uplift
      };
    });
  };

  const handleFileUpload = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const csvText = e.target?.result as string;
        const data = parseCSV(csvText);
        onDataLoaded(data);
        setDataInfo({ count: data.length, source: file.name });
      } catch (error) {
        console.error('Error parsing CSV:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    reader.readAsText(file);
  }, [onDataLoaded]);

  const loadLiveEcosystemData = () => {
    setIsLoading(true);
    
    // LIVE DATA ONLY - Use real ecosystem metrics, no random generation
    const data: FieldMetric[] = [];
    const baseTime = Date.now();
    
    // Use real coherence and harmonic lock from ecosystem
    const coherenceValue = metrics.coherence || 0;
    const harmonicLockValue = metrics.harmonicLock ? 1 : 0;
    const probabilityValue = metrics.probabilityFusion || 0;
    
    // Create single current data point (no simulated history)
    data.push({
      time: baseTime,
      entropy: 1 - coherenceValue,
      coherence: coherenceValue,
      schumannLock: harmonicLockValue,
      probabilityUplift: probabilityValue,
    });
    
    setTimeout(() => {
      onDataLoaded(data);
      setDataInfo({ count: data.length, source: 'Live Ecosystem Data (Real-time)' });
      setIsLoading(false);
    }, 100);
  };

  const downloadSampleCSV = () => {
    // LIVE DATA ONLY - Use real current ecosystem values
    const coherence = metrics.coherence || 0;
    const harmonicLock = metrics.harmonicLock ? 1 : 0;
    const probability = metrics.probabilityFusion || 0;
    
    const csvContent = [
      'time,entropy,coherence,schumannLock,probabilityUplift',
      `${Date.now()},${(1 - coherence).toFixed(4)},${coherence.toFixed(4)},${harmonicLock},${probability.toFixed(4)}`
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'field_pull_sample.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          Field Data Loader
          {isInitialized && (
            <Badge variant="outline" className="ml-2">Ecosystem Connected</Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-3">
          <div className="flex items-center gap-2">
            <Input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={isLoading}
              className="flex-1"
            />
            <Button
              variant="default"
              size="sm"
              onClick={loadLiveEcosystemData}
              disabled={isLoading || !isInitialized}
            >
              <Upload className="h-4 w-4 mr-1" />
              Live
            </Button>
          </div>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={downloadSampleCSV}
            className="w-full"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Sample CSV
          </Button>
        </div>

        {dataInfo && (
          <div className="flex items-center justify-between p-3 bg-muted rounded-lg">
            <div>
              <div className="font-medium text-sm">Data Loaded</div>
              <div className="text-xs text-muted-foreground">{dataInfo.source}</div>
            </div>
            <Badge variant="secondary">{dataInfo.count} points</Badge>
          </div>
        )}

        {isLoading && (
          <div className="flex items-center justify-center p-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
          </div>
        )}
        
        {/* Show current ecosystem metrics */}
        {isInitialized && (
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-muted rounded">
              <div className="text-muted-foreground">Coherence</div>
              <div className="font-bold">{(metrics.coherence * 100).toFixed(1)}%</div>
            </div>
            <div className="p-2 bg-muted rounded">
              <div className="text-muted-foreground">Harmonic Lock</div>
              <div className="font-bold">{metrics.harmonicLock ? '🔒 Locked' : 'Unlocked'}</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
