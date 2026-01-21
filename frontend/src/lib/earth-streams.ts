// Enhanced Earth Data Streams with Solar Wind and Geomagnetic Field Integration

export interface SolarWindData {
  velocity: number; // km/s
  density: number; // protons/cm³
  temperature: number; // Kelvin
  magneticField: number; // nT
  pressure: number; // nPa
  timestamp: number;
}

export interface GeomagneticData {
  kpIndex: number; // 0-9 scale
  apIndex: number; // nT
  dstIndex: number; // nT
  fieldStrength: number; // nT
  inclination: number; // degrees
  declination: number; // degrees
  timestamp: number;
}

export interface AtmosphericData {
  ionosphericDensity: number;
  electronicContent: number; // TEC
  scintillationIndex: number;
  timestamp: number;
}

export interface EarthStreamMetrics {
  solarWind: SolarWindData;
  geomagnetic: GeomagneticData;
  atmospheric: AtmosphericData;
  coherenceIndex: number;
  fieldCoupling: number;
}

export class EarthStreamsMonitor {
  private solarWindData: SolarWindData | null = null;
  private geomagneticData: GeomagneticData | null = null;
  private atmosphericData: AtmosphericData | null = null;
  private isActive: boolean = false;

  initialize(): void {
    console.log('🌍 Initializing Earth Streams Monitor...');
    this.startSolarWindMonitoring();
    this.startGeomagneticMonitoring();
    this.startAtmosphericMonitoring();
    this.isActive = true;
  }

  private startSolarWindMonitoring(): void {
    setInterval(() => {
      this.updateSolarWindData();
    }, 2000); // Update every 2 seconds
  }

  private startGeomagneticMonitoring(): void {
    setInterval(() => {
      this.updateGeomagneticData();
    }, 1500); // Update every 1.5 seconds
  }

  private startAtmosphericMonitoring(): void {
    setInterval(() => {
      this.updateAtmosphericData();
    }, 3000); // Update every 3 seconds
  }

  private updateSolarWindData(): void {
    const time = Date.now();
    
    // Simulate realistic solar wind variations
    const baseVelocity = 400; // km/s typical
    const velocityVariation = Math.sin(time / 20000) * 100 + Math.random() * 50;
    
    const baseDensity = 5; // protons/cm³
    const densityVariation = Math.cos(time / 15000) * 2 + Math.random() * 1;
    
    this.solarWindData = {
      velocity: Math.max(250, baseVelocity + velocityVariation),
      density: Math.max(1, baseDensity + densityVariation),
      temperature: 100000 + Math.sin(time / 25000) * 50000 + Math.random() * 20000,
      magneticField: 3 + Math.sin(time / 18000) * 2 + Math.random() * 1,
      pressure: 1.5 + Math.cos(time / 12000) * 0.8 + Math.random() * 0.3,
      timestamp: time
    };
  }

  private updateGeomagneticData(): void {
    const time = Date.now();
    
    // Simulate geomagnetic field variations
    const baseKp = 2; // Quiet conditions
    const stormInfluence = Math.sin(time / 30000) * 2 + Math.random() * 1;
    
    this.geomagneticData = {
      kpIndex: Math.max(0, Math.min(9, baseKp + stormInfluence)),
      apIndex: 10 + Math.sin(time / 22000) * 15 + Math.random() * 5,
      dstIndex: -20 + Math.cos(time / 35000) * 30 + Math.random() * 10,
      fieldStrength: 50000 + Math.sin(time / 40000) * 2000 + Math.random() * 500,
      inclination: 65 + Math.sin(time / 60000) * 2,
      declination: 12 + Math.cos(time / 50000) * 1,
      timestamp: time
    };
  }

  private updateAtmosphericData(): void {
    const time = Date.now();
    
    this.atmosphericData = {
      ionosphericDensity: 1e12 + Math.sin(time / 28000) * 5e11 + Math.random() * 2e11,
      electronicContent: 20 + Math.cos(time / 32000) * 10 + Math.random() * 5,
      scintillationIndex: 0.2 + Math.sin(time / 18000) * 0.15 + Math.random() * 0.05,
      timestamp: time
    };
  }

  getEarthStreamMetrics(): EarthStreamMetrics | null {
    if (!this.solarWindData || !this.geomagneticData || !this.atmosphericData) {
      return null;
    }

    const coherenceIndex = this.calculateCoherenceIndex();
    const fieldCoupling = this.calculateFieldCoupling();

    return {
      solarWind: this.solarWindData,
      geomagnetic: this.geomagneticData,
      atmospheric: this.atmosphericData,
      coherenceIndex,
      fieldCoupling
    };
  }

  private calculateCoherenceIndex(): number {
    if (!this.solarWindData || !this.geomagneticData) return 0.5;
    
    // Calculate coherence based on solar wind-magnetosphere coupling
    const velocityFactor = Math.min(1, this.solarWindData.velocity / 600);
    const densityFactor = Math.min(1, this.solarWindData.density / 10);
    const kpFactor = 1 - (this.geomagneticData.kpIndex / 9);
    
    return (velocityFactor * 0.4 + densityFactor * 0.3 + kpFactor * 0.3);
  }

  private calculateFieldCoupling(): number {
    if (!this.solarWindData || !this.geomagneticData || !this.atmosphericData) return 1.0;
    
    // Multi-layer field coupling calculation
    const solarCoupling = this.solarWindData.magneticField / 10;
    const geomagneticCoupling = this.geomagneticData.fieldStrength / 60000;
    const ionosphericCoupling = 1 - this.atmosphericData.scintillationIndex;
    
    return Math.min(2.0, solarCoupling + geomagneticCoupling + ionosphericCoupling);
  }

  isMonitoringActive(): boolean {
    return this.isActive;
  }
}

export const earthStreamsMonitor = new EarthStreamsMonitor();

// Simplified interface for components
export interface SimpleEarthStreams {
  solarWindVelocity: number;
  geomagneticKp: number;
  ionosphericDensity: number;
  fieldCoupling: number;
}

export async function getEarthStreams(): Promise<SimpleEarthStreams> {
  const metrics = earthStreamsMonitor.getEarthStreamMetrics();
  
  if (!metrics) {
    // Initialize if not started
    earthStreamsMonitor.initialize();
    return {
      solarWindVelocity: 400,
      geomagneticKp: 2,
      ionosphericDensity: 50,
      fieldCoupling: 1.2
    };
  }
  
  return {
    solarWindVelocity: metrics.solarWind.velocity,
    geomagneticKp: metrics.geomagnetic.kpIndex,
    ionosphericDensity: metrics.atmospheric.ionosphericDensity / 1e10, // Normalize
    fieldCoupling: metrics.fieldCoupling
  };
}