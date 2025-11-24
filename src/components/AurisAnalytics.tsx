import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

export const AurisAnalytics = () => {
  const [aurisData, setAurisData] = useState({
    compilationRate: 0.87,
    symbolProcessing: 0.94,
    quantumEntanglement: 0.76,
    dataIntegrity: 0.99
  });

  const [symbols, setSymbols] = useState([
    { symbol: '◯', frequency: 7.83, resonance: 0.95, active: true },
    { symbol: '∞', frequency: 108, resonance: 0.89, active: true },
    { symbol: '👁', frequency: 111, resonance: 0.72, active: false },
    { symbol: '△', frequency: 144, resonance: 0.84, active: false },
    { symbol: '◊', frequency: 432, resonance: 0.91, active: true },
    { symbol: '□', frequency: 432, resonance: 0.88, active: true },
    { symbol: '☆', frequency: 528, resonance: 0.93, active: true },
    { symbol: '✡', frequency: 639, resonance: 0.86, active: true },
    { symbol: '⚇', frequency: 729, resonance: 0.75, active: false },
    { symbol: '⚡', frequency: 741, resonance: 0.82, active: false },
    { symbol: '✺', frequency: 852, resonance: 0.79, active: false },
    { symbol: '🌀', frequency: 852, resonance: 0.81, active: false },
    { symbol: '☥', frequency: 963, resonance: 0.87, active: true },
    { symbol: '⭐', frequency: 963, resonance: 0.90, active: true },
    { symbol: '✝', frequency: 697.5, resonance: 0.85, active: true }
  ]);

  const [streamData, setStreamData] = useState({
    packetsProcessed: 15847,
    errorRate: 0.003,
    throughput: 2.4,
    latency: 12
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setAurisData(prev => ({
        compilationRate: Math.max(0.1, prev.compilationRate + (Math.random() - 0.5) * 0.02),
        symbolProcessing: Math.max(0.1, prev.symbolProcessing + (Math.random() - 0.5) * 0.01),
        quantumEntanglement: Math.max(0.1, prev.quantumEntanglement + (Math.random() - 0.5) * 0.03),
        dataIntegrity: Math.max(0.95, prev.dataIntegrity + (Math.random() - 0.5) * 0.005)
      }));

      setSymbols(prev => prev.map(s => ({
        ...s,
        resonance: Math.max(0.1, s.resonance + (Math.random() - 0.5) * 0.05),
        active: Math.random() > 0.3
      })));

      setStreamData(prev => ({
        packetsProcessed: prev.packetsProcessed + Math.floor(Math.random() * 10),
        errorRate: Math.max(0, prev.errorRate + (Math.random() - 0.5) * 0.001),
        throughput: Math.max(0.1, prev.throughput + (Math.random() - 0.5) * 0.1),
        latency: Math.max(1, prev.latency + (Math.random() - 0.5) * 2)
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Compilation Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {(aurisData.compilationRate * 100).toFixed(1)}%
            </div>
            <Progress value={aurisData.compilationRate * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Symbol Processing</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(aurisData.symbolProcessing * 100).toFixed(1)}%
            </div>
            <Progress value={aurisData.symbolProcessing * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Quantum Link</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {(aurisData.quantumEntanglement * 100).toFixed(1)}%
            </div>
            <Progress value={aurisData.quantumEntanglement * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Data Integrity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(aurisData.dataIntegrity * 100).toFixed(1)}%
            </div>
            <Progress value={aurisData.dataIntegrity * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Active Symbols</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {symbols.map((symbol, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-2xl">{symbol.symbol}</div>
                    <div className="text-sm text-gray-600">
                      {symbol.frequency} Hz
                    </div>
                    <Badge variant={symbol.active ? "default" : "secondary"}>
                      {symbol.active ? "Active" : "Idle"}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm w-12">{(symbol.resonance * 100).toFixed(0)}%</span>
                    <Progress value={symbol.resonance * 100} className="w-20" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Stream Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Packets Processed</span>
                <span className="font-bold">{streamData.packetsProcessed.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Error Rate</span>
                <span className="font-bold text-red-600">{(streamData.errorRate * 100).toFixed(3)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Throughput</span>
                <span className="font-bold text-green-600">{streamData.throughput.toFixed(1)} MB/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Latency</span>
                <span className="font-bold text-blue-600">{streamData.latency.toFixed(0)} ms</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AurisAnalytics;