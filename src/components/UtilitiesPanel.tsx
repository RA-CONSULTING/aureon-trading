import React, { useState } from 'react';
// import { motion } from 'framer-motion';
import { Card } from './ui/card';
import { Button } from './ui/button';

export const UtilitiesPanel: React.FC<{ tool: string }> = ({ tool }) => {
  const [exportStatus, setExportStatus] = useState<'idle' | 'exporting' | 'complete'>('idle');
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('csv');

  const handleExport = async () => {
    setExportStatus('exporting');
    
    // Simulate export process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Create sample data
    const data = Array.from({ length: 100 }, (_, i) => ({
      timestamp: Date.now() + i * 1000,
      phi: Math.sin(i * 0.1) * 0.8,
      kappa: Math.cos(i * 0.15) * 0.6,
      psi: Math.sin(i * 0.2) * Math.exp(-i * 0.01),
      tsv: Math.random() * 0.5
    }));

    let content: string;
    let filename: string;
    let mimeType: string;

    if (exportFormat === 'csv') {
      const headers = 'timestamp,phi,kappa,psi,tsv\n';
      const rows = data.map(row => 
        `${row.timestamp},${row.phi.toFixed(6)},${row.kappa.toFixed(6)},${row.psi.toFixed(6)},${row.tsv.toFixed(6)}`
      ).join('\n');
      content = headers + rows;
      filename = 'harmonic_nexus_data.csv';
      mimeType = 'text/csv';
    } else {
      content = JSON.stringify(data, null, 2);
      filename = 'harmonic_nexus_data.json';
      mimeType = 'application/json';
    }

    // Create and trigger download
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setExportStatus('complete');
    setTimeout(() => setExportStatus('idle'), 3000);
  };

  const renderExportTool = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">Export Simulation Data</h4>
      
      <div className="space-y-3">
        <div>
          <label className="text-sm font-medium text-slate-600 mb-2 block">Export Format</label>
          <div className="flex gap-2">
            <Button
              variant={exportFormat === 'csv' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setExportFormat('csv')}
            >
              CSV
            </Button>
            <Button
              variant={exportFormat === 'json' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setExportFormat('json')}
            >
              JSON
            </Button>
          </div>
        </div>
        
        <div className="p-3 bg-slate-50 rounded-lg">
          <div className="text-sm text-slate-600 mb-1">Export includes:</div>
          <ul className="text-xs text-slate-500 space-y-1">
            <li>• Timestamp data</li>
            <li>• φ (Phase) values</li>
            <li>• κ (Coherence) measurements</li>
            <li>• ψ (Amplitude) evolution</li>
            <li>• TSV (Tensor Symmetry Values)</li>
          </ul>
        </div>
        
        <Button 
          onClick={handleExport}
          disabled={exportStatus === 'exporting'}
          className="w-full"
        >
          {exportStatus === 'exporting' && (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2 animate-spin" />
          )}
          {exportStatus === 'idle' && `Export as ${exportFormat.toUpperCase()}`}
          {exportStatus === 'exporting' && 'Exporting...'}
          {exportStatus === 'complete' && '✓ Export Complete'}
        </Button>
        
        {exportStatus === 'complete' && (
          <div className="p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full" />
              <span className="text-green-700 text-sm font-medium">
                Data exported successfully
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderSaveVisualization = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">Save Visualization</h4>
      
      <div className="grid grid-cols-2 gap-3">
        <Button variant="outline" className="h-auto p-3">
          <div className="text-center">
            <div className="text-2xl mb-1">📊</div>
            <div className="text-sm">Save Chart</div>
          </div>
        </Button>
        
        <Button variant="outline" className="h-auto p-3">
          <div className="text-center">
            <div className="text-2xl mb-1">🌐</div>
            <div className="text-sm">Save 3D View</div>
          </div>
        </Button>
        
        <Button variant="outline" className="h-auto p-3">
          <div className="text-center">
            <div className="text-2xl mb-1">📸</div>
            <div className="text-sm">Screenshot</div>
          </div>
        </Button>
        
        <Button variant="outline" className="h-auto p-3">
          <div className="text-center">
            <div className="text-2xl mb-1">🎬</div>
            <div className="text-sm">Record GIF</div>
          </div>
        </Button>
      </div>
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">System Settings</h4>
      
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
          <span className="text-sm text-slate-700">High-precision timing</span>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
        
        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
          <span className="text-sm text-slate-700">Real-time data streaming</span>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
        
        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
          <span className="text-sm text-slate-700">Symbolic compiler active</span>
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
        </div>
        
        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
          <span className="text-sm text-slate-700">Phase lock enabled</span>
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
        </div>
      </div>
    </div>
  );

  switch (tool) {
    case 'export':
      return <Card>{renderExportTool()}</Card>;
    case 'saveviz':
      return <Card>{renderSaveVisualization()}</Card>;
    case 'settings':
      return <Card>{renderSettings()}</Card>;
    default:
      return <Card><div className="p-8 text-center text-slate-500">Select a utility tool</div></Card>;
  }
};