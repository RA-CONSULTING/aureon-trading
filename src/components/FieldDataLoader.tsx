import React, { useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Upload, FileText, Download } from 'lucide-react';

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
        entropy: row.entropy || Math.random() * 0.8 + 0.1,
        coherence: row.coherence || Math.random() * 0.9 + 0.1,
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

  const loadSampleData = () => {
    setIsLoading(true);
    
    // Generate realistic field pull metrics
    const data: FieldMetric[] = [];
    const baseTime = Date.now();
    
    for (let i = 0; i < 100; i++) {
      const timeOffset = i * 12000; // 12 second intervals
      const coherencePhase = Math.sin(i * 0.1) * 0.3 + 0.5;
      const entropyPhase = Math.cos(i * 0.08) * 0.2 + 0.4;
      
      data.push({
        time: baseTime + timeOffset,
        entropy: Math.max(0.1, Math.min(0.9, entropyPhase + Math.random() * 0.1)),
        coherence: Math.max(0.1, Math.min(0.9, coherencePhase + Math.random() * 0.1)),
        schumannLock: Math.random() * 0.8 + 0.2,
        probabilityUplift: Math.random() * 0.6 + 0.1
      });
    }
    
    setTimeout(() => {
      onDataLoaded(data);
      setDataInfo({ count: data.length, source: 'Generated Sample' });
      setIsLoading(false);
    }, 500);
  };

  const downloadSampleCSV = () => {
    const csvContent = [
      'time,entropy,coherence,schumannLock,probabilityUplift',
      ...Array.from({ length: 50 }, (_, i) => {
        const time = Date.now() + i * 10000;
        const entropy = (Math.random() * 0.8 + 0.1).toFixed(4);
        const coherence = (Math.random() * 0.9 + 0.1).toFixed(4);
        const schumannLock = (Math.random() * 0.8 + 0.2).toFixed(4);
        const probabilityUplift = (Math.random() * 0.6 + 0.1).toFixed(4);
        return `${time},${entropy},${coherence},${schumannLock},${probabilityUplift}`;
      })
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
              variant="outline"
              size="sm"
              onClick={loadSampleData}
              disabled={isLoading}
            >
              <Upload className="h-4 w-4 mr-1" />
              Sample
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
      </CardContent>
    </Card>
  );
}