import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { FileText, Download, Play, Database, Activity } from 'lucide-react';
import LiveValidationDashboard from './LiveValidationDashboard';

interface CSVStats {
  filename: string;
  rows: number;
  lastUpdate: string;
  size: string;
  status: 'active' | 'idle' | 'error';
}

export default function EvidenceAuditPanel() {
  const [csvStats, setCSVStats] = useState<CSVStats[]>([
    {
      filename: 'auris_metrics.csv',
      rows: 1247,
      lastUpdate: '2 sec ago',
      size: '156 KB',
      status: 'active'
    },
    {
      filename: 'aura_features.csv', 
      rows: 1198,
      lastUpdate: '3 sec ago',
      size: '89 KB',
      status: 'active'
    },
    {
      filename: 'validation_snapshots.csv',
      rows: 23,
      lastUpdate: '45 sec ago', 
      size: '12 KB',
      status: 'idle'
    }
  ]);

  const [auditLog, setAuditLog] = useState([
    { time: '14:23:15', event: 'Validation protocol started', type: 'info' },
    { time: '14:23:47', event: 'Coherence threshold reached (0.67)', type: 'success' },
    { time: '14:24:12', event: 'Snapshot captured - Intent Block 1', type: 'success' },
    { time: '14:25:33', event: 'Schumann lock achieved (0.71)', type: 'success' },
    { time: '14:26:01', event: 'TSV gain approaching limit (0.89)', type: 'warning' }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCSVStats(prev => prev.map(stat => ({
        ...stat,
        rows: stat.status === 'active' ? stat.rows + Math.floor(Math.random() * 3) : stat.rows,
        lastUpdate: stat.status === 'active' ? 
          `${Math.floor(Math.random() * 10) + 1} sec ago` : stat.lastUpdate
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <Tabs defaultValue="validation" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="validation">Live Validation</TabsTrigger>
          <TabsTrigger value="csv">CSV Logging</TabsTrigger>
          <TabsTrigger value="snapshots">Snapshots</TabsTrigger>
          <TabsTrigger value="audit">Audit Trail</TabsTrigger>
        </TabsList>

        <TabsContent value="validation">
          <LiveValidationDashboard />
        </TabsContent>

        <TabsContent value="csv" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="w-5 h-5" />
                CSV Data Streams
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {csvStats.map(stat => (
                <div key={stat.filename} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <FileText className="w-4 h-4 text-muted-foreground" />
                    <div>
                      <div className="font-medium">{stat.filename}</div>
                      <div className="text-xs text-muted-foreground">
                        {stat.rows.toLocaleString()} rows • {stat.size}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-muted-foreground">{stat.lastUpdate}</div>
                    <Badge variant={stat.status === 'active' ? 'default' : 'secondary'}>
                      {stat.status}
                    </Badge>
                  </div>
                </div>
              ))}

              <Button className="w-full">
                <Download className="w-4 h-4 mr-2" />
                Export All CSV Files
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="snapshots" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Evidence Snapshots</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground text-center py-8">
                Snapshot capture feature coming soon
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                {auditLog.map((log, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-2 rounded-lg hover:bg-muted/50">
                    <div className="text-xs text-muted-foreground min-w-[60px]">{log.time}</div>
                    <div className="text-sm flex-1">{log.event}</div>
                    <Badge variant={
                      log.type === 'success' ? 'default' : 
                      log.type === 'warning' ? 'secondary' : 
                      'outline'
                    }>
                      {log.type}
                    </Badge>
                  </div>
                ))}
              </div>

              <Button className="w-full">
                <FileText className="w-4 h-4 mr-2" />
                Export Audit Log
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}