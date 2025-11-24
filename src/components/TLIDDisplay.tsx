import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Copy, Shield, Clock } from 'lucide-react';
import { useState } from 'react';

interface TLIDDisplayProps {
  tlid: string;
  name?: string;
  dob?: string;
  date?: string;
}

export function TLIDDisplay({ tlid, name, dob, date }: TLIDDisplayProps) {
  const [copied, setCopied] = useState(false);

  const copyTLID = async () => {
    await navigator.clipboard.writeText(tlid);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Parse TLID components
  const parts = tlid.split('-');
  const prefix = parts[0]; // NX
  const dateStamp = parts[1]; // 20250902
  const initials = parts[2]; // GL
  const segments = parts.slice(3); // P3Y5, J3IV, CXIB, TKX6

  const formatDate = (dateStr: string) => {
    if (dateStr.length === 8) {
      return `${dateStr.slice(6, 8)}/${dateStr.slice(4, 6)}/${dateStr.slice(0, 4)}`;
    }
    return dateStr;
  };

  return (
    <Card className="border-2 border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-indigo-800">
          <Shield className="w-5 h-5" />
          Temporal Lattice ID (TLID)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 p-3 bg-white/60 rounded-lg border">
          <code className="flex-1 font-mono text-sm font-bold text-indigo-900 tracking-wider">
            {tlid}
          </code>
          <button
            onClick={copyTLID}
            className="p-1 hover:bg-indigo-100 rounded transition-colors"
            title="Copy TLID"
          >
            <Copy className="w-4 h-4 text-indigo-600" />
          </button>
          {copied && (
            <Badge variant="secondary" className="text-xs">
              Copied!
            </Badge>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-indigo-100 text-indigo-800">
                {prefix}
              </Badge>
              <span className="text-gray-600">Nexus Source Law</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Clock className="w-3 h-3 text-gray-500" />
              <code className="text-indigo-700">{formatDate(dateStamp)}</code>
              <span className="text-gray-600">Anchor Date</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-purple-100 text-purple-800">
                {initials}
              </Badge>
              <span className="text-gray-600">Identity</span>
            </div>
            
            <div className="flex flex-wrap gap-1">
              {segments.map((seg, i) => (
                <code key={i} className="text-xs px-1 py-0.5 bg-gray-100 rounded text-gray-700">
                  {seg}
                </code>
              ))}
            </div>
          </div>
        </div>

        <div className="pt-2 border-t border-indigo-100">
          <div className="text-xs text-gray-600 space-y-1">
            <div className="font-mono">
              Hash({name} + {dob} + {formatDate(dateStamp)} + Nexus:10-9-1 + Peace+Joy)
            </div>
            <div className="text-indigo-700 font-medium">
              🔒 Cryptographic proof of temporal session state
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}