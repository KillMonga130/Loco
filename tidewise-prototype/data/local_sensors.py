"""
Simulated Local Sensors
Mimics TideWise hardware sensors until we have real Raspberry Pi deployment
"""

import numpy as np
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOCATION, SENSOR_NOISE_LEVEL, DEBUG

class LocalSensors:
    """Simulates local TideWise sensor readings"""
    
    def __init__(self):
        self.location = LOCATION['name']
        # Baseline "normal" values for Port Elizabeth
        self.baseline_pressure = 1013.0  # hPa
        self.baseline_tide = 1.5  # meters above datum
        self.baseline_temp = 18.0  # °C (average ocean temp)
        self.baseline_wave_height = 0.8  # meters
        
    def get_readings(self):
        """
        Simulate sensor readings with realistic noise
        
        In a real deployment, this would read from:
        - BME280 pressure sensor
        - Ultrasonic tide gauge
        - DS18B20 temperature sensor  
        - MPU6050 accelerometer (for wave motion)
        """
        
        # Add small random variations to simulate real sensor noise
        pressure = self.baseline_pressure + np.random.normal(0, SENSOR_NOISE_LEVEL * 10)
        tide_level = self.baseline_tide + np.random.normal(0, SENSOR_NOISE_LEVEL * 2)
        water_temp = self.baseline_temp + np.random.normal(0, SENSOR_NOISE_LEVEL * 5)
        wave_height = max(0, self.baseline_wave_height + np.random.normal(0, SENSOR_NOISE_LEVEL * 3))
        
        # Calculate wave period (inverse of frequency)
        wave_period = 6.0 + np.random.normal(0, 0.5)  # seconds
        
        data = {
            'timestamp': datetime.utcnow(),
            'pressure_hpa': round(pressure, 1),
            'tide_level_m': round(tide_level, 2),
            'water_temp_c': round(water_temp, 1),
            'wave_height_m': round(wave_height, 2),
            'wave_period_s': round(wave_period, 1),
            'sensor_status': 'OK',
            'battery_voltage': 12.4,  # Simulated battery level
            'solar_charging': True,
            'source': 'SIMULATED LOCAL SENSORS'
        }
        
        if DEBUG:
            print(f"\n📡 LOCAL SENSOR READINGS:")
            print(f"   Pressure: {data['pressure_hpa']} hPa")
            print(f"   Tide Level: {data['tide_level_m']} m")
            print(f"   Water Temp: {data['water_temp_c']} °C")
            print(f"   Wave Height: {data['wave_height_m']} m")
            print(f"   Wave Period: {data['wave_period_s']} s")
            print(f"   Status: {data['sensor_status']}")
        
        return data
    
    def simulate_storm_conditions(self, storm_intensity=0.5):
        """
        Simulate what sensors would read during a storm
        storm_intensity: 0.0 (calm) to 1.0 (extreme storm)
        """
        # During storms:
        # - Pressure drops significantly
        # - Tide level rises (surge)
        # - Water temp drops (cold upwelling)
        # - Wave height increases dramatically
        
        pressure_drop = storm_intensity * 20  # Up to -20 hPa
        tide_surge = storm_intensity * 2.5  # Up to +2.5m surge
        temp_drop = storm_intensity * 3  # Up to -3°C
        wave_increase = storm_intensity * 4  # Up to +4m waves
        
        self.baseline_pressure = 1013.0 - pressure_drop
        self.baseline_tide = 1.5 + tide_surge
        self.baseline_temp = 18.0 - temp_drop
        self.baseline_wave_height = 0.8 + wave_increase
        
        if DEBUG:
            print(f"\n⚠️  SIMULATING STORM CONDITIONS (Intensity: {storm_intensity*100:.0f}%)")
        
        return self.get_readings()
    
    def reset_to_normal(self):
        """Reset to calm ocean conditions"""
        self.baseline_pressure = 1013.0
        self.baseline_tide = 1.5
        self.baseline_temp = 18.0
        self.baseline_wave_height = 0.8
        
        if DEBUG:
            print(f"\n🌊 RESET TO NORMAL CONDITIONS")

def test_sensors():
    """Test the simulated sensors"""
    print("=" * 60)
    print("TESTING SIMULATED LOCAL SENSORS")
    print("=" * 60)
    
    sensors = LocalSensors()
    
    # Test 1: Normal conditions
    print("\n🌊 Test 1: Normal Ocean Conditions")
    normal_data = sensors.get_readings()
    
    # Test 2: Moderate storm
    print("\n⛈️  Test 2: Moderate Storm (50% intensity)")
    moderate_storm = sensors.simulate_storm_conditions(storm_intensity=0.5)
    
    # Test 3: Severe storm
    print("\n🌀 Test 3: Severe Storm (90% intensity)")
    severe_storm = sensors.simulate_storm_conditions(storm_intensity=0.9)
    
    # Reset
    sensors.reset_to_normal()
    
    print("\n✅ Sensor simulation working!\n")
    
    return {
        'normal': normal_data,
        'moderate_storm': moderate_storm,
        'severe_storm': severe_storm
    }

if __name__ == "__main__":
    test_sensors()
