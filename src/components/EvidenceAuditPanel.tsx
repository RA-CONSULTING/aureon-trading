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
                <div className="text-xs text-purple-300">Feature vectors</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm text-purple-400">Current Session</div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" />
                <span className="text-green-400 text-sm">Active logging</span>
                <Badge variant="outline" className="border-green-500 text-green-400 ml-auto">
                  Real-time
                </Badge>
              </div>
            </div>

            <Button className="w-full bg-purple-600 hover:bg-purple-700">
              <Download className="w-4 h-4 mr-2" />
              Export CSV Files
            </Button>
          </TabsContent>

          <TabsContent value="snapshots" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm text-purple-400">
                Last snapshot: {lastSnapshot ? lastSnapshot.toLocaleTimeString() : 'None'}
              </div>
              <Button onClick={handleSnapshot} className="bg-purple-600 hover:bg-purple-700">
                <Camera className="w-4 h-4 mr-2" />
                Take Snapshot
              </Button>
            </div>

            <div className="space-y-2">
              <div className="text-sm text-purple-400">Recent Snapshots</div>
              {recentSnapshots.map(snapshot => (
                <div key={snapshot.id} className="bg-black/60 p-3 rounded border border-purple-500/20">
                  <div className="flex items-center justify-between text-xs">
                    <div className="text-purple-300">{snapshot.timestamp}</div>
                    <Badge variant="outline" className="border-purple-500/30">
                      {snapshot.intent}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mt-2 text-xs">
                    <div>
                      <span className="text-purple-400">Lock:</span>
                      <span className="text-green-400 ml-1">{snapshot.lock}</span>
                    </div>
                    <div>
                      <span className="text-purple-400">Coherence:</span>
                      <span className="text-green-400 ml-1">{snapshot.coherence}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="audit" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm text-purple-400">Total Entries</div>
                <div className="text-2xl font-mono text-blue-400">{auditEntries}</div>
              </div>
              <div className="space-y-2">
                <div className="text-sm text-purple-400">Latency</div>
                <div className="text-2xl font-mono text-green-400">&lt;10ms</div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm text-purple-400">System Status</div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">WebSocket Bridge</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">Validators Online</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-3 h-3 text-green-400" />
                  <span className="text-green-400">CSV Writers</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-3 h-3 text-yellow-400" />
                  <span className="text-yellow-400">Unity Timeline</span>
                </div>
              </div>
            </div>

            <Button className="w-full bg-blue-600 hover:bg-blue-700">
              <FileText className="w-4 h-4 mr-2" />
              Generate Audit Report
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}