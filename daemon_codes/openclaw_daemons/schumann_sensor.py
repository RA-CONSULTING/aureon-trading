#!/usr/bin/env python3
"""
Schumann Resonance Sensor Acquisition System
Reads real ELF magnetic field data from DIY induction coil + ADC.
Supports both hardware mode (real sensor) and simulation mode (realistic testing).

Hardware: ADS1256 24-bit ADC via SPI on Raspberry Pi
          or any sound card with line input + preamp
"""
import numpy as np
import json
import time
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, List, Tuple, Callable
from collections import deque
import os

# Optional hardware imports (graceful fallback if not on Pi)
try:
    import spidev
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False


class ADS1256Driver:
    """Driver for ADS1256 24-bit ADC via SPI.
    
    Wiring (Raspberry Pi):
    - VCC → 3.3V (Pin 1)
    - GND → GND (Pin 6)
    - SCLK → GPIO11/SCLK (Pin 23)
    - DIN → GPIO10/MOSI (Pin 19)
    - DOUT → GPIO9/MISO (Pin 21)
    - CS → GPIO8/CE0 (Pin 24)
    - DRDY → GPIO17 (Pin 11) — data ready interrupt
    """
    
    # ADS1256 registers
    REG_STATUS = 0x00
    REG_MUX = 0x01
    REG_ADCON = 0x02
    REG_DRATE = 0x03
    REG_IO = 0x04
    REG_OFC0 = 0x05
    REG_OFC1 = 0x06
    REG_OFC2 = 0x07
    REG_FSC0 = 0x08
    REG_FSC1 = 0x09
    REG_FSC2 = 0x0A
    
    # Commands
    CMD_WAKEUP = 0x00
    CMD_RDATA = 0x01
    CMD_RDATAC = 0x03
    CMD_SDATAC = 0x0F
    CMD_RREG = 0x10
    CMD_WREG = 0x50
    CMD_SELFCAL = 0xF0
    CMD_SELFOCAL = 0xF1
    CMD_SELFGCAL = 0xF2
    CMD_SYSOCAL = 0xF3
    CMD_SYSGCAL = 0xF4
    CMD_SYNC = 0xFC
    CMD_STANDBY = 0xFD
    CMD_RESET = 0xFE
    
    # Data rates (Hz)
    DRATES = {
        30000: 0xF0,
        15000: 0xE0,
        7500: 0xD0,
        3750: 0xC0,
        2000: 0xB0,
        1000: 0xA1,
        500: 0x92,
        100: 0x82,
        60: 0x72,
        50: 0x63,
        30: 0x53,
        25: 0x43,
        15: 0x33,
        10: 0x23,
        5: 0x13,
        2: 0x03,
    }
    
    def __init__(self, bus: int = 0, device: int = 0, drdy_pin: int = 17, 
                 data_rate: int = 100, gain: int = 1):
        self.bus = bus
        self.device = device
        self.drdy_pin = drdy_pin
        self.data_rate = data_rate
        self.gain = gain
        self.spi = None
        self.initialized = False
        
        if not HARDWARE_AVAILABLE:
            raise RuntimeError("RPi.GPIO and spidev not available. Not running on Raspberry Pi.")
    
    def init(self):
        """Initialize ADC hardware."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.drdy_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.spi = spidev.SpiDev()
        self.spi.open(self.bus, self.device)
        self.spi.max_speed_hz = 1920000
        self.spi.mode = 1
        
        self._reset()
        self._configure()
        self.initialized = True
        print("✅ ADS1256 initialized")
    
    def _reset(self):
        """Send reset command."""
        self.spi.xfer2([self.CMD_RESET])
        time.sleep(0.01)
    
    def _configure(self):
        """Configure ADC registers."""
        # Set data rate
        self._write_register(self.REG_DRATE, [self.DRATES.get(self.data_rate, 0x82)])
        
        # Set gain
        adcon = (self.gain & 0x07) << 4
        self._write_register(self.REG_ADCON, [adcon])
        
        # Set MUX to AIN0-AINCOM (single-ended)
        self._write_register(self.REG_MUX, [0x01])
        
        # Auto-calibrate
        self.spi.xfer2([self.CMD_SELFCAL])
        time.sleep(0.01)
    
    def _write_register(self, reg: int, values: List[int]):
        """Write to ADC register."""
        self.spi.xfer2([self.CMD_WREG | reg, len(values) - 1] + values)
        time.sleep(0.01)
    
    def _read_register(self, reg: int, n: int = 1) -> List[int]:
        """Read from ADC register."""
        return self.spi.xfer2([self.CMD_RREG | reg, n - 1] + [0x00] * n)[2:]
    
    def wait_for_data_ready(self, timeout: float = 1.0):
        """Wait for DRDY pin to go low."""
        start = time.time()
        while GPIO.input(self.drdy_pin) == GPIO.HIGH:
            if time.time() - start > timeout:
                raise TimeoutError("DRDY timeout")
            time.sleep(0.0001)
    
    def read_raw(self) -> int:
        """Read single 24-bit sample."""
        self.wait_for_data_ready()
        
        # Send RDATA command
        resp = self.spi.xfer2([self.CMD_RDATA, 0x00, 0x00, 0x00])
        
        # Parse 24-bit two's complement
        raw = (resp[1] << 16) | (resp[2] << 8) | resp[3]
        if raw & 0x800000:
            raw -= 0x1000000
        
        return raw
    
    def read_voltage(self) -> float:
        """Read voltage (±VREF based on gain)."""
        raw = self.read_raw()
        vref = 2.5  # Assuming 2.5V reference
        return raw * (2 * vref) / (self.gain * 0x7FFFFF)
    
    def read_buffer(self, n_samples: int, sample_rate: Optional[int] = None) -> np.ndarray:
        """Read N samples at specified rate."""
        if sample_rate is None:
            sample_rate = self.data_rate
        
        samples = np.zeros(n_samples)
        interval = 1.0 / sample_rate
        
        for i in range(n_samples):
            samples[i] = self.read_voltage()
            if i < n_samples - 1:
                time.sleep(interval)
        
        return samples
    
    def close(self):
        """Cleanup hardware."""
        if self.spi:
            self.spi.close()
        GPIO.cleanup()


class SchumannSimulator:
    """Generates realistic Schumann resonance data for testing.
    
    Models:
    - Fundamental: 7.83 Hz + harmonics
    - Daily variation (diurnal cycle)
    - Solar activity modulation
    - Random atmospheric noise
    - Occasional anomalies (sferics, sprites)
    """
    
    SCHUMANN_FREQS = [7.83, 14.1, 20.3, 26.4, 32.5, 38.6]  # Hz
    HARMONIC_AMPLITUDES = [1.0, 0.45, 0.25, 0.15, 0.10, 0.07]  # Relative
    
    def __init__(self, sample_rate: int = 128, noise_floor: float = 1e-9):
        self.sample_rate = sample_rate
        self.noise_floor = noise_floor
        self.t = 0.0
        self.phase_offsets = np.random.uniform(0, 2 * np.pi, len(self.SCHUMANN_FREQS))
        self._init_diurnal_params()
    
    def _init_diurnal_params(self):
        """Initialize diurnal variation parameters."""
        # Schumann amplitude varies by ~20% over 24h
        # Peak around 14:00 UTC (global thunderstorm maximum)
        self.diurnal_amp = 0.2
        self.diurnal_phase = 14.0  # UTC hour of peak
        
        # Solar cycle (simplified 11-year cycle, currently near maximum)
        self.solar_factor = 1.15
    
    def _diurnal_modulation(self, timestamp: Optional[float] = None) -> float:
        """Compute diurnal amplitude modulation."""
        if timestamp is None:
            timestamp = time.time()
        
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        hour = dt.hour + dt.minute / 60.0
        
        # Cosine variation peaking at diurnal_phase
        angle = 2 * np.pi * (hour - self.diurnal_phase) / 24.0
        modulation = 1.0 + self.diurnal_amp * np.cos(angle)
        
        return modulation * self.solar_factor
    
    def read(self, n_samples: int) -> np.ndarray:
        """Generate N realistic Schumann samples."""
        t_now = time.time()
        modulation = self._diurnal_modulation(t_now)
        
        # Time array
        dt = 1.0 / self.sample_rate
        t = np.arange(n_samples) * dt + self.t
        self.t = t[-1] + dt
        
        # Generate signal
        signal = np.zeros(n_samples)
        
        for freq, amp, phase in zip(
            self.SCHUMANN_FREQS, 
            self.HARMONIC_AMPLITUDES,
            self.phase_offsets
        ):
            signal += amp * modulation * np.sin(2 * np.pi * freq * t + phase)
        
        # Add noise
        noise = np.random.normal(0, self.noise_floor, n_samples)
        
        # Add occasional sferic (atmospheric transient)
        if np.random.random() < 0.01:  # 1% chance per buffer
            sferic_idx = np.random.randint(0, n_samples)
            sferic_amp = np.random.uniform(0.5, 2.0) * modulation
            signal[sferic_idx] += sferic_amp
        
        return signal + noise
    
    def get_ground_truth(self) -> Dict:
        """Return current ground truth parameters."""
        t_now = time.time()
        dt = datetime.fromtimestamp(t_now, tz=timezone.utc)
        
        return {
            "timestamp": dt.isoformat(),
            "fundamental_freq": self.SCHUMANN_FREQS[0],
            "fundamental_amp": self.HARMONIC_AMPLITUDES[0] * self._diurnal_modulation(t_now),
            "modulation": self._diurnal_modulation(t_now),
            "solar_factor": self.solar_factor,
            "utc_hour": dt.hour + dt.minute / 60.0,
        }


class SchumannSensor:
    """Main sensor interface — handles both real hardware and simulation."""
    
    def __init__(self, mode: str = "sim", sample_rate: int = 128, 
                 buffer_size: int = 1024, calibration_file: Optional[str] = None):
        """
        Args:
            mode: "sim" for simulation, "hw" for hardware, "soundcard" for audio input
            sample_rate: Sampling rate in Hz
            buffer_size: Number of samples per read
            calibration_file: Path to calibration coefficients JSON
        """
        self.mode = mode
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.calibration_file = calibration_file or "sensor_calibration.json"
        
        self.adc: Optional[ADS1256Driver] = None
        self.simulator: Optional[SchumannSimulator] = None
        self.calibration: Dict = {}
        
        # FFT parameters
        self.fft_size = 2048
        self.freq_bins = np.fft.rfftfreq(self.fft_size, 1.0 / sample_rate)
        
        # Ring buffer for continuous processing
        self._ring_buffer = deque(maxlen=self.fft_size)
        
        # Callbacks
        self._callbacks: List[Callable] = []
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self._init_mode()
        self._load_calibration()
    
    def _init_mode(self):
        """Initialize hardware or simulation."""
        if self.mode == "hw":
            if not HARDWARE_AVAILABLE:
                print("⚠️ Hardware libraries not available. Falling back to simulation.")
                self.mode = "sim"
                self.simulator = SchumannSimulator(self.sample_rate)
            else:
                try:
                    self.adc = ADS1256Driver(data_rate=self.sample_rate)
                    self.adc.init()
                except Exception as e:
                    print(f"⚠️ Hardware init failed: {e}. Falling back to simulation.")
                    self.mode = "sim"
                    self.simulator = SchumannSimulator(self.sample_rate)
        
        elif self.mode == "sim":
            self.simulator = SchumannSimulator(self.sample_rate)
            print(f"✅ Simulator initialized (sample_rate={self.sample_rate} Hz)")
        
        elif self.mode == "soundcard":
            print("🎵 Soundcard mode: use external ADC (e.g., USB audio interface)")
            print("   Connect preamp output to line input")
            # Would need sounddevice/pyaudio here
    
    def _load_calibration(self):
        """Load calibration coefficients."""
        if os.path.exists(self.calibration_file):
            with open(self.calibration_file, 'r') as f:
                self.calibration = json.load(f)
            print(f"✅ Loaded calibration from {self.calibration_file}")
        else:
            print(f"ℹ️ No calibration file found: {self.calibration_file}")
            print("   Run calibrate() to generate one")
    
    def calibrate(self, n_samples: int = 10000) -> Dict:
        """Run calibration procedure.
        
        Measures:
        - Offset (zero-field)
        - Gain (known reference signal)
        - Noise floor
        - Frequency response
        """
        print("🔧 Running calibration...")
        
        cal = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "sample_rate": self.sample_rate,
        }
        
        if self.mode == "sim":
            # Simulator calibration — just verify parameters
            cal["offset"] = 0.0
            cal["gain"] = 1.0
            cal["noise_floor"] = self.simulator.noise_floor
            cal["freq_response"] = {f: 1.0 for f in self.simulator.SCHUMANN_FREQS}
        
        else:
            # Hardware calibration
            print("  1. Measuring offset (short input)...")
            offset_samples = self._read_raw(n_samples // 10)
            cal["offset"] = float(np.mean(offset_samples))
            cal["noise_floor"] = float(np.std(offset_samples))
            
            print("  2. Noise floor: {:.2e} V".format(cal["noise_floor"]))
            print("  3. Gain: 1.0 (unity, adjust for your coil)")
            cal["gain"] = 1.0
        
        self.calibration = cal
        
        with open(self.calibration_file, 'w') as f:
            json.dump(cal, f, indent=2)
        
        print(f"✅ Calibration saved to {self.calibration_file}")
        return cal
    
    def _read_raw(self, n_samples: int) -> np.ndarray:
        """Read raw samples from active source."""
        if self.mode == "sim" and self.simulator:
            return self.simulator.read(n_samples)
        elif self.mode == "hw" and self.adc:
            return self.adc.read_buffer(n_samples, self.sample_rate)
        else:
            raise RuntimeError("No sensor source available")
    
    def read(self) -> np.ndarray:
        """Read calibrated samples."""
        raw = self._read_raw(self.buffer_size)
        
        # Apply calibration
        offset = self.calibration.get("offset", 0.0)
        gain = self.calibration.get("gain", 1.0)
        
        calibrated = (raw - offset) / gain
        
        # Add to ring buffer
        self._ring_buffer.extend(calibrated)
        
        return calibrated
    
    def get_spectrum(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute FFT spectrum of ring buffer contents.
        
        Returns:
            (frequencies, magnitudes)
        """
        if len(self._ring_buffer) < self.fft_size:
            # Pad with zeros if not enough data
            data = np.zeros(self.fft_size)
            n = len(self._ring_buffer)
            data[-n:] = list(self._ring_buffer)
        else:
            data = np.array(list(self._ring_buffer)[-self.fft_size:])
        
        # Window
        window = np.hanning(len(data))
        data_windowed = data * window
        
        # FFT
        spectrum = np.fft.rfft(data_windowed)
        magnitude = np.abs(spectrum) / (len(data) / 2)
        
        return self.freq_bins, magnitude
    
    def detect_peaks(self) -> List[Dict]:
        """Detect Schumann resonance peaks in current spectrum.
        
        Returns list of peak dicts with keys:
            freq, amplitude, snr, is_harmonic, harmonic_n
        """
        freqs, mags = self.get_spectrum()
        
        peaks = []
        fundamental = 7.83
        
        for n, expected_freq in enumerate([7.83, 14.1, 20.3, 26.4, 32.5, 38.6], 1):
            # Find peak near expected frequency (±0.5 Hz tolerance)
            mask = (freqs >= expected_freq - 0.5) & (freqs <= expected_freq + 0.5)
            if not np.any(mask):
                continue
            
            idx = np.argmax(mags[mask])
            peak_freq = freqs[mask][idx]
            peak_amp = mags[mask][idx]
            
            # Estimate SNR (peak vs local noise floor)
            noise_mask = (freqs >= expected_freq - 2.0) & (freqs <= expected_freq + 2.0) & ~mask
            noise_floor = np.mean(mags[noise_mask]) if np.any(noise_mask) else 1e-10
            snr = peak_amp / noise_floor if noise_floor > 0 else 0
            
            peaks.append({
                "freq": float(peak_freq),
                "amplitude": float(peak_amp),
                "snr": float(snr),
                "is_harmonic": n > 1,
                "harmonic_n": n,
            })
        
        return peaks
    
    def get_schumann_field_strength(self) -> Dict:
        """Get current Schumann field measurement.
        
        Returns dict compatible with HNC daemon:
            schumann: fundamental frequency in Hz
            amplitude: pT (estimated)
            coherence: peak sharpness / SNR metric
            quality: overall signal quality 0-1
        """
        peaks = self.detect_peaks()
        
        if not peaks:
            return {
                "schumann": 7.83,
                "amplitude": 0.0,
                "coherence": 0.0,
                "quality": 0.0,
                "peaks": [],
            }
        
        fundamental = peaks[0]
        
        # Compute coherence from peak sharpness and harmonic presence
        n_harmonics = sum(1 for p in peaks if p["is_harmonic"] and p["snr"] > 3)
        coherence = fundamental["snr"] / (1 + fundamental["snr"])  # Normalize
        
        # Quality combines coherence and harmonic richness
        quality = coherence * (1 + 0.1 * n_harmonics) / 1.5
        quality = min(1.0, quality)
        
        # Convert amplitude to pT (very rough estimate, needs proper calibration)
        # For a typical coil: 1 V ≈ 1 nT = 1000 pT at 7.83 Hz
        # This is placeholder — real calibration needed
        amplitude_pt = fundamental["amplitude"] * 1000.0
        
        return {
            "schumann": fundamental["freq"],
            "amplitude": float(amplitude_pt),
            "coherence": float(coherence),
            "quality": float(quality),
            "peaks": peaks,
        }
    
    def register_callback(self, callback: Callable):
        """Register callback for continuous mode."""
        self._callbacks.append(callback)
    
    def start_continuous(self):
        """Start continuous acquisition in background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._acquisition_loop, daemon=True)
        self._thread.start()
        print("✅ Continuous acquisition started")
    
    def stop_continuous(self):
        """Stop continuous acquisition."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("🛑 Continuous acquisition stopped")
    
    def _acquisition_loop(self):
        """Background acquisition loop."""
        while self._running:
            try:
                samples = self.read()
                measurement = self.get_schumann_field_strength()
                
                for callback in self._callbacks:
                    try:
                        callback(measurement, samples)
                    except Exception as e:
                        print(f"⚠️ Callback error: {e}")
                
                time.sleep(0.1)  # 10 Hz update rate
            
            except Exception as e:
                print(f"⚠️ Acquisition error: {e}")
                time.sleep(1.0)
    
    def close(self):
        """Cleanup resources."""
        self.stop_continuous()
        if self.adc:
            self.adc.close()


def demo():
    """Demo the sensor in simulation mode."""
    print("=" * 60)
    print("🌍 Schumann Sensor Demo (Simulation Mode)")
    print("=" * 60)
    
    sensor = SchumannSensor(mode="sim", sample_rate=128, buffer_size=512)
    
    # Calibrate
    sensor.calibrate()
    
    # Take some readings
    print("\n📊 Taking measurements...")
    for i in range(10):
        samples = sensor.read()
        freqs, mags = sensor.get_spectrum()
        peaks = sensor.detect_peaks()
        field = sensor.get_schumann_field_strength()
        
        print(f"\n   Sample {i+1}:")
        print(f"   Fundamental: {field['schumann']:.2f} Hz")
        print(f"   Amplitude: {field['amplitude']:.2f} pT")
        print(f"   Coherence: {field['coherence']:.3f}")
        print(f"   Quality: {field['quality']:.3f}")
        print(f"   Harmonics detected: {len([p for p in peaks if p['is_harmonic']])}")
        
        time.sleep(1.0)
    
    sensor.close()
    print("\n✅ Demo complete")


if __name__ == "__main__":
    demo()
