import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

export const EarthLiveAnalytics = () => {
  const [earthData, setEarthData] = useState({
    magneticField: 0.89,
    ionosphereActivity: 0.76,
    solarWind: 0.82,
    geomagneticIndex: 0.67
  });

  const [sensorData, setSensorData] = useState([
    { id: 'MAG-01', location: 'Arctic', value: 54.2, status: 'active' },
    { id: 'MAG-02', location: 'Antarctic', value: 48.7, status: 'active' },
    { id: 'ION-01', location: 'Equatorial', value: 312.5, status: 'warning' },
    { id: 'SOL-01', location: 'Solar Monitor', value: 425.8, status: 'active' }
  ]);

  const [streamStats, setStreamStats] = useState({
    dataPoints: 24847,
    updateRate: 2.1,
    accuracy: 0.987,
    coverage: 0.94
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setEarthData(prev => ({
        magneticField: Math.max(0.1, prev.magneticField + (Math.random() - 0.5) * 0.02),
        ionosphereActivity: Math.max(0.1, prev.ionosphereActivity + (Math.random() - 0.5) * 0.03),
        solarWind: Math.max(0.1, prev.solarWind + (Math.random() - 0.5) * 0.04),
        geomagneticIndex: Math.max(0.1, prev.geomagneticIndex + (Math.random() - 0.5) * 0.02)
      }));

      setSensorData(prev => prev.map(s => ({
        ...s,
        value: Math.max(10, s.value + (Math.random() - 0.5) * 20),
        status: Math.random() > 0.8 ? 'warning' : 'active'
      })));

      setStreamStats(prev => ({
        dataPoints: prev.dataPoints + Math.floor(Math.random() * 5),
        updateRate: Math.max(0.5, prev.updateRate + (Math.random() - 0.5) * 0.2),
        accuracy: Math.max(0.95, prev.accuracy + (Math.random() - 0.5) * 0.005),
        coverage: Math.max(0.8, prev.coverage + (Math.random() - 0.5) * 0.01)
      }));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Magnetic Field</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {(earthData.magneticField * 100).toFixed(1)}%
            </div>
            <Progress value={earthData.magneticField * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Ionosphere</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(earthData.ionosphereActivity * 100).toFixed(1)}%
            </div>
            <Progress value={earthData.ionosphereActivity * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Solar Wind</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {(earthData.solarWind * 100).toFixed(1)}%
            </div>
            <Progress value={earthData.solarWind * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Geomagnetic Index</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(earthData.geomagneticIndex * 100).toFixed(1)}%
            </div>
            <Progress value={earthData.geomagneticIndex * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Sensor Network</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {sensorData.map((sensor, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Badge variant={sensor.status === 'active' ? "default" : "destructive"}>
                      {sensor.id}
                    </Badge>
                    <div className="text-sm text-gray-600">
                      {sensor.location}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-bold">{sensor.value.toFixed(1)}</span>
                    <div className={`w-3 h-3 rounded-full ${
                      sensor.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'
                    }`} />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Stream Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Data Points</span>
                <span className="font-bold">{streamStats.dataPoints.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Update Rate</span>
                <span className="font-bold text-green-600">{streamStats.updateRate.toFixed(1)} Hz</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Accuracy</span>
                <span className="font-bold text-blue-600">{(streamStats.accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Coverage</span>
                <span className="font-bold text-purple-600">{(streamStats.coverage * 100).toFixed(1)}%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default EarthLiveAnalytics;