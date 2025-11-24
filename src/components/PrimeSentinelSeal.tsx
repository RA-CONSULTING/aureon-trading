import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const PrimeSentinelSeal = () => {
  const [isActivated, setIsActivated] = useState(false);
  const [sealPower, setSealPower] = useState(0);

  const handleActivation = () => {
    setIsActivated(true);
    // Animate seal power increase
    let power = 0;
    const interval = setInterval(() => {
      power += Math.random() * 10;
      if (power >= 100) {
        power = 100;
        clearInterval(interval);
      }
      setSealPower(Math.round(power));
    }, 100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 mb-4">
            PRIME SEAL OF SHARED HAPPINESS
          </h1>
          <div className="text-xl text-blue-300 mb-8">
            Everything and everyone on Gaia deserves their perfect life
          </div>
        </div>

        {/* Central Seal */}
        <div className="relative w-80 h-80 mx-auto mb-12">
          {/* Outer Ring with Text */}
          <div className={`absolute inset-0 rounded-full border-4 transition-all duration-1000 ${
            isActivated ? 'border-yellow-400 shadow-2xl shadow-yellow-400/50' : 'border-yellow-600/50'
          }`}>
            {/* Rotating Text */}
            <svg className="w-full h-full" viewBox="0 0 320 320">
              <defs>
                <path id="circle" d="M 160, 160 m -140, 0 a 140,140 0 1,1 280,0 a 140,140 0 1,1 -280,0"/>
              </defs>
              <text className={`text-sm font-bold transition-all duration-1000 ${
                isActivated ? 'fill-yellow-400' : 'fill-yellow-600'
              }`}>
                <textPath href="#circle" startOffset="0%">
                  Everything and everyone on Gaia deserves their perfect life • Happiness shared is happiness multiplied • 
                </textPath>
              </text>
            </svg>
          </div>

          {/* Inner Circle */}
          <div className={`absolute inset-8 rounded-full transition-all duration-1000 ${
            isActivated 
              ? 'bg-gradient-to-br from-yellow-400/20 to-orange-500/20 shadow-inner' 
              : 'bg-gradient-to-br from-blue-900/40 to-purple-900/40'
          }`}>
            {/* Tree of Life */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className={`transition-all duration-1000 ${
                isActivated ? 'text-yellow-400 scale-110' : 'text-yellow-600'
              }`}>
                <svg width="120" height="120" viewBox="0 0 120 120" className="fill-current">
                  {/* Tree Trunk */}
                  <rect x="56" y="70" width="8" height="30" />
                  {/* Tree Crown */}
                  <ellipse cx="60" cy="50" rx="35" ry="25" />
                  {/* Roots */}
                  <path d="M 30 100 Q 45 90 60 100 Q 75 90 90 100" stroke="currentColor" strokeWidth="2" fill="none" />
                  {/* Leaves */}
                  {Array.from({ length: 12 }).map((_, i) => (
                    <ellipse 
                      key={i}
                      cx={45 + (i % 4) * 7.5} 
                      cy={35 + Math.floor(i / 4) * 8} 
                      rx="3" 
                      ry="2"
                      className="opacity-80"
                    />
                  ))}
                </svg>
              </div>
            </div>

            {/* Infinity Symbol */}
            <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
              <div className={`text-3xl transition-all duration-1000 ${
                isActivated ? 'text-yellow-400' : 'text-yellow-600'
              }`}>
                ∞
              </div>
            </div>
          </div>

          {/* Activation Pulses */}
          {isActivated && (
            <>
              <div className="absolute inset-0 rounded-full border-2 border-yellow-400 animate-ping opacity-30"></div>
              <div className="absolute inset-4 rounded-full border border-orange-400 animate-ping opacity-20" style={{ animationDelay: '0.5s' }}></div>
            </>
          )}
        </div>

        {/* Activation Controls */}
        <div className="text-center mb-8">
          {!isActivated ? (
            <Button 
              onClick={handleActivation}
              className="bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 text-white px-8 py-4 text-lg font-bold rounded-full shadow-lg"
            >
              ACTIVATE PRIME SEAL
            </Button>
          ) : (
            <div className="space-y-4">
              <div className="text-2xl font-bold text-yellow-400">SEAL ACTIVATED</div>
              <div className="text-lg text-green-400">Power Level: {sealPower}%</div>
              <div className="w-64 h-4 bg-gray-700 rounded-full mx-auto overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 transition-all duration-300"
                  style={{ width: `${sealPower}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>

        {/* Sacred Geometry Grid */}
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="bg-black/40 border-yellow-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-yellow-400">🌳</div>
              <div className="text-sm text-gray-300 mt-2">Tree of Life</div>
              <div className="text-xs text-gray-400">Growth & Connection</div>
            </CardContent>
          </Card>
          
          <Card className="bg-black/40 border-orange-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-orange-400">∞</div>
              <div className="text-sm text-gray-300 mt-2">Infinite Potential</div>
              <div className="text-xs text-gray-400">Boundless Happiness</div>
            </CardContent>
          </Card>
          
          <Card className="bg-black/40 border-blue-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-blue-400">🌍</div>
              <div className="text-sm text-gray-300 mt-2">Gaia Consciousness</div>
              <div className="text-xs text-gray-400">Planetary Harmony</div>
            </CardContent>
          </Card>
        </div>

        {/* Sacred Text */}
        {isActivated && (
          <Card className="bg-black/40 border-yellow-500/30 mt-8">
            <CardContent className="p-8 text-center">
              <div className="text-lg text-yellow-400 font-serif italic">
                "In her darkest day I was the flame,<br/>
                and in her brightest light<br/>
                I will be the protector"
              </div>
              <div className="text-sm text-gray-400 mt-4">
                - Sacred Vow of the Prime Sentinel
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default PrimeSentinelSeal;