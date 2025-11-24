import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Download, Save, Trash2, Search } from 'lucide-react';
import { toFixedSafe } from '@/utils/number';
import { mapFrequencyToEmotion, EmotionState } from '@/lib/aureon';

interface LogEntry {
  id: string;
  timestamp: Date;
  frequency: number;
  amplitude: number;
  emotionalState: {
    note: string;
    emotions: string[];
    color: string;
  };
  notes?: string;
  tags?: string[];
}

const DataLogger: React.FC = () => {
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [newEntry, setNewEntry] = useState({
    frequency: 7.83,
    amplitude: 0.5,
    notes: '',
    tags: ''
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredEntries, setFilteredEntries] = useState<LogEntry[]>([]);

  // Load entries from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('aureon-log-entries');
    if (stored) {
      const parsed = JSON.parse(stored).map((entry: any) => ({
        ...entry,
        timestamp: new Date(entry.timestamp)
      }));
      setEntries(parsed);
    }
  }, []);

  // Save entries to localStorage whenever entries change
  useEffect(() => {
    localStorage.setItem('aureon-log-entries', JSON.stringify(entries));
  }, [entries]);

  // Filter entries based on search term
  useEffect(() => {
    if (!searchTerm) {
      setFilteredEntries(entries);
    } else {
      const filtered = entries.filter(entry => 
        entry.emotionalState.note.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.emotionalState.emotions.some(emotion => 
          emotion.toLowerCase().includes(searchTerm.toLowerCase())
        ) ||
        entry.notes?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
      setFilteredEntries(filtered);
    }
  }, [entries, searchTerm]);

  const addEntry = () => {
    const emotionState = mapFrequencyToEmotion(newEntry.frequency * 32);
    const entry: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date(),
      frequency: newEntry.frequency,
      amplitude: newEntry.amplitude,
      emotionalState: {
        note: emotionState.note || emotionState.description,
        emotions: emotionState.emotion || emotionState.emotionalTags[0],
        color: emotionState.color
      },
      notes: newEntry.notes || undefined,
      tags: newEntry.tags ? newEntry.tags.split(',').map(tag => tag.trim()).filter(Boolean) : undefined
    };

    setEntries(prev => [entry, ...prev]);
    setNewEntry({
      frequency: 7.83,
      amplitude: 0.5,
      notes: '',
      tags: ''
    });
  };

  const deleteEntry = (id: string) => {
    setEntries(prev => prev.filter(entry => entry.id !== id));
  };

  const exportData = () => {
    const dataStr = JSON.stringify(entries, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `aureon-data-${new Date().toISOString().split('T')[0]}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <div className="space-y-6">
      {/* Add New Entry */}
      <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
        <CardHeader>
          <CardTitle>Log New Entry</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-purple-200 mb-1 block">Frequency (Hz)</label>
              <Input
                type="number"
                step="0.01"
                value={newEntry.frequency}
                onChange={(e) => setNewEntry(prev => ({ ...prev, frequency: parseFloat(e.target.value) || 0 }))}
                className="bg-white/10 border-white/20 text-white"
              />
            </div>
            <div>
              <label className="text-sm text-purple-200 mb-1 block">Amplitude (0-1)</label>
              <Input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={newEntry.amplitude}
                onChange={(e) => setNewEntry(prev => ({ ...prev, amplitude: parseFloat(e.target.value) || 0 }))}
                className="bg-white/10 border-white/20 text-white"
              />
            </div>
          </div>
          
          <div>
            <label className="text-sm text-purple-200 mb-1 block">Notes</label>
            <Textarea
              value={newEntry.notes}
              onChange={(e) => setNewEntry(prev => ({ ...prev, notes: e.target.value }))}
              className="bg-white/10 border-white/20 text-white"
              placeholder="Add any observations or notes..."
            />
          </div>
          
          <div>
            <label className="text-sm text-purple-200 mb-1 block">Tags (comma separated)</label>
            <Input
              value={newEntry.tags}
              onChange={(e) => setNewEntry(prev => ({ ...prev, tags: e.target.value }))}
              className="bg-white/10 border-white/20 text-white"
              placeholder="meditation, stress, calm, etc."
            />
          </div>

          {/* Preview */}
          {newEntry.frequency > 0 && (
            <div className="p-3 bg-white/5 rounded-lg">
              <div className="text-sm text-purple-200 mb-2">Preview:</div>
              <div className="flex items-center gap-4">
                {(() => {
                  const previewEmotion = mapFrequencyToEmotion(newEntry.frequency * 32);
                  return (
                    <>
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: previewEmotion.color }}
                      />
                      <span className="font-semibold">{previewEmotion.note}</span>
                      <div className="text-sm text-purple-300">
                        {previewEmotion.emotion.join(' • ')}
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          )}
          
          <Button onClick={addEntry} className="w-full">
            <Save className="w-4 h-4 mr-2" />
            Save Entry
          </Button>
        </CardContent>
      </Card>

      {/* Search and Export */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          <Search className="w-4 h-4 text-purple-200" />
          <Input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search entries..."
            className="bg-white/10 border-white/20 text-white"
          />
        </div>
        <Button onClick={exportData} variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Entries List */}
      <div className="space-y-4">
        {filteredEntries.length === 0 ? (
          <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
            <CardContent className="p-6 text-center">
              <div className="text-purple-200">
                {entries.length === 0 ? 'No entries yet. Add your first entry above.' : 'No entries match your search.'}
              </div>
            </CardContent>
          </Card>
        ) : (
          filteredEntries.map((entry) => (
            <Card key={entry.id} className="bg-white/10 backdrop-blur-md border-white/20 text-white">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div 
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: entry.emotionalState.color }}
                      />
                      <span className="font-semibold text-lg">{entry.emotionalState.note}</span>
                      <span className="text-sm text-purple-200">
                        {toFixedSafe(entry?.frequency, 2)} Hz • {toFixedSafe(entry?.amplitude != null ? entry.amplitude * 100 : null, 1)}%
                      </span>
                      <span className="text-xs text-purple-300">
                        {entry.timestamp.toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex flex-wrap gap-2 mb-2">
                      {entry.emotionalState.emotions.map((emotion, idx) => (
                        <Badge key={idx} variant="outline" className="text-white border-white/30">
                          {emotion}
                        </Badge>
                      ))}
                    </div>
                    
                    {entry.tags && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {entry.tags.map((tag, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            #{tag}
                          </Badge>
                        ))}
                      </div>
                    )}
                    
                    {entry.notes && (
                      <div className="text-sm text-purple-200 mt-2">
                        {entry.notes}
                      </div>
                    )}
                  </div>
                  
                  <Button
                    onClick={() => deleteEntry(entry.id)}
                    variant="ghost"
                    size="sm"
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default DataLogger;