import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { getEmotionalStateFromFrequency } from '@/lib/schumann-emotional-mapping';
import { toFixedSafe } from '@/utils/number';

interface DayData {
  date: string;
  frequency: number;
  amplitude: number;
  emotionalState: any;
  activity: string;
}

const mapFrequencyToEmotion = (freq: number) => {
  return getEmotionalStateFromFrequency(freq);
}

const CalendarView: React.FC = () => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [monthData, setMonthData] = useState<DayData[]>([]);
  const [selectedDay, setSelectedDay] = useState<DayData | null>(null);

  // Generate sample data for the current month
  useEffect(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    const data: DayData[] = [];
    for (let day = 1; day <= daysInMonth; day++) {
      const freq = 7.83 + (Math.random() - 0.5) * 3;
      const amplitude = 0.2 + Math.random() * 0.6;
      const emotionalState = mapFrequencyToEmotion(freq * 32); // Scale to audible range
      
      data.push({
        date: `${year}-${(month + 1).toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`,
        frequency: freq,
        amplitude,
        emotionalState,
        activity: amplitude > 0.6 ? 'High' : amplitude > 0.4 ? 'Moderate' : 'Low'
      });
    }
    
    setMonthData(data);
  }, [currentDate]);

  const navigateMonth = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentDate);
    if (direction === 'prev') {
      newDate.setMonth(newDate.getMonth() - 1);
    } else {
      newDate.setMonth(newDate.getMonth() + 1);
    }
    setCurrentDate(newDate);
    setSelectedDay(null);
  };

  const getDayOfWeek = (dateString: string) => {
    return new Date(dateString).getDay();
  };

  const formatMonth = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  return (
    <div className="space-y-6">
      {/* Calendar Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">{formatMonth(currentDate)}</h2>
        <div className="flex gap-2">
          <Button onClick={() => navigateMonth('prev')} variant="outline" size="sm">
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button onClick={() => navigateMonth('next')} variant="outline" size="sm">
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar Grid */}
        <div className="lg:col-span-2">
          <Card className="bg-white/10 backdrop-blur-md border-white/20">
            <CardContent className="p-4">
              {/* Days of week header */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                  <div key={day} className="text-center text-sm font-semibold text-purple-200 p-2">
                    {day}
                  </div>
                ))}
              </div>
              
              {/* Calendar days */}
              <div className="grid grid-cols-7 gap-1">
                {/* Empty cells for days before month starts */}
                {Array.from({ length: getDayOfWeek(monthData[0]?.date || '') }).map((_, idx) => (
                  <div key={`empty-${idx}`} className="h-16"></div>
                ))}
                
                {/* Month days */}
                {monthData.map((dayData, idx) => (
                  <button
                    key={dayData.date}
                    onClick={() => setSelectedDay(dayData)}
                    className="h-16 p-1 rounded-lg border border-white/20 bg-white/5 hover:bg-white/10 transition-colors relative"
                    style={{ 
                      borderColor: dayData.emotionalState.color,
                      borderWidth: selectedDay?.date === dayData.date ? '2px' : '1px'
                    }}
                  >
                    <div className="text-xs text-white font-semibold">
                      {new Date(dayData.date).getDate()}
                    </div>
                    <div 
                      className="w-2 h-2 rounded-full mx-auto mt-1"
                      style={{ backgroundColor: dayData.emotionalState.color }}
                    />
                    <div className="text-xs text-purple-200 mt-1">
                      {dayData.emotionalState.note}
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Day Details */}
        <div className="space-y-4">
          {selectedDay ? (
            <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
              <CardHeader>
                <CardTitle>
                  {new Date(selectedDay.date).toLocaleDateString('en-US', { 
                    weekday: 'long', 
                    month: 'long', 
                    day: 'numeric' 
                  })}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-purple-200">Frequency</div>
                    <div className="text-lg font-semibold">{toFixedSafe(selectedDay.frequency, 2)} Hz</div>
                  </div>
                  <div>
                    <div className="text-sm text-purple-200">Amplitude</div>
                    <div className="text-lg font-semibold">{toFixedSafe(selectedDay.amplitude * 100, 1)}%</div>
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-purple-200 mb-2">Aureon Note</div>
                  <div 
                    className="text-xl font-bold p-2 rounded-lg text-center"
                    style={{ backgroundColor: selectedDay.emotionalState.color + '20', color: selectedDay.emotionalState.color }}
                  >
                    {selectedDay.emotionalState.note}
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-purple-200 mb-2">Emotional State</div>
                  <div className="flex flex-wrap gap-2">
                    {selectedDay.emotionalState.emotion.map((emotion, idx) => (
                      <Badge key={idx} variant="outline" className="text-white border-white/30">
                        {emotion}
                      </Badge>

                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="text-sm text-purple-200 mb-2">Activity Level</div>
                  <Badge className={
                    selectedDay.activity === 'High' ? 'bg-red-500' :
                    selectedDay.activity === 'Moderate' ? 'bg-yellow-500' : 'bg-green-500'
                  }>
                    {selectedDay.activity}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
              <CardContent className="p-6 text-center">
                <div className="text-purple-200">Select a day to view details</div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default CalendarView;