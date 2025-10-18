"""
TideWise Data Manager
Combines NOAA regional data + local sensor data for comprehensive ocean intelligence
"""

from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DEBUG, THRESHOLDS
from data.noaa_gfs import NOAAGFSFetcher
from data.local_sensors import LocalSensors

class TideWiseDataManager:
    """
    Orchestrates all data sources and provides unified ocean intelligence
    """
    
    def __init__(self):
        self.noaa_fetcher = NOAAGFSFetcher()
        self.local_sensors = LocalSensors()
        self.data_history = []  # Store readings for trend analysis
        
    def get_current_conditions(self):
        """
        Fetch all available data from NOAA + local sensors
        Returns unified dataset
        """
        if DEBUG:
            print("\n" + "=" * 60)
            print("TIDEWISE DATA MANAGER - FETCHING ALL DATA")
            print("=" * 60)
        
        # Fetch regional data (NOAA)
        regional_data = self.noaa_fetcher.fetch_pressure_and_wind()
        
        # Fetch local sensor data
        local_data = self.local_sensors.get_readings()
        
        # Combine into unified dataset
        unified_data = {
            'timestamp': datetime.utcnow(),
            
            # Atmospheric pressure (compare regional vs local)
            'regional_pressure_hpa': regional_data['pressure_hpa'],
            'local_pressure_hpa': local_data['pressure_hpa'],
            'pressure_difference': local_data['pressure_hpa'] - regional_data['pressure_hpa'],
            
            # Wind (regional only - unless we add anemometer)
            'wind_speed_ms': regional_data['wind_speed_ms'],
            'wind_direction': regional_data['wind_direction'],
            
            # Local ocean conditions
            'tide_level_m': local_data['tide_level_m'],
            'water_temp_c': local_data['water_temp_c'],
            'wave_height_m': local_data['wave_height_m'],
            'wave_period_s': local_data['wave_period_s'],
            
            # System status
            'sensor_status': local_data['sensor_status'],
            'data_sources': [regional_data['source'], local_data['source']]
        }
        
        # Store for trend analysis
        self.data_history.append(unified_data)
        
        # Keep only last 72 hours of data (for 3-day trend analysis)
        if len(self.data_history) > 720:  # 72 hours * 10 readings/hour
            self.data_history.pop(0)
        
        if DEBUG:
            self._print_unified_data(unified_data)
        
        return unified_data
    
    def calculate_trends(self, hours_back=3):
        """
        Calculate trends over the past N hours
        Returns pressure drop, tide rise, etc.
        """
        if len(self.data_history) < 2:
            return None
        
        # Get data from N hours ago (if available)
        target_time = datetime.utcnow() - timedelta(hours=hours_back)
        
        # Find closest historical reading
        past_data = None
        for data in self.data_history:
            if data['timestamp'] <= target_time:
                past_data = data
        
        if past_data is None:
            past_data = self.data_history[0]  # Use oldest available
        
        current_data = self.data_history[-1]
        
        trends = {
            'hours_analyzed': (current_data['timestamp'] - past_data['timestamp']).total_seconds() / 3600,
            'pressure_drop_hpa': past_data['local_pressure_hpa'] - current_data['local_pressure_hpa'],
            'tide_rise_m': current_data['tide_level_m'] - past_data['tide_level_m'],
            'temp_change_c': current_data['water_temp_c'] - past_data['water_temp_c'],
            'wave_height_increase_m': current_data['wave_height_m'] - past_data['wave_height_m']
        }
        
        if DEBUG:
            print(f"\n📈 TRENDS (past {trends['hours_analyzed']:.1f} hours):")
            print(f"   Pressure change: {trends['pressure_drop_hpa']:+.1f} hPa")
            print(f"   Tide change: {trends['tide_rise_m']:+.2f} m")
            print(f"   Temp change: {trends['temp_change_c']:+.1f} °C")
            print(f"   Wave height change: {trends['wave_height_increase_m']:+.2f} m")
        
        return trends
    
    def assess_risk_level(self):
        """
        Analyze current conditions + trends to determine alert level
        Returns: 'green', 'yellow', 'orange', or 'red'
        """
        if len(self.data_history) < 2:
            return {
                'level': 'green',
                'risk_score': 0,
                'message': '✅ NORMAL: No immediate flood risk',
                'reasons': ['Insufficient data for trend analysis'],
                'current_conditions': self.data_history[-1] if self.data_history else {},
                'trends': None
            }
        
        current = self.data_history[-1]
        trends = self.calculate_trends(hours_back=3)
        
        # Risk factors
        risk_score = 0
        risk_reasons = []
        
        # Factor 1: Rapid pressure drop
        if trends['pressure_drop_hpa'] >= THRESHOLDS['red']['pressure_drop_3h']:
            risk_score += 3
            risk_reasons.append(f"Severe pressure drop: {trends['pressure_drop_hpa']:.1f} hPa in 3h")
        elif trends['pressure_drop_hpa'] >= THRESHOLDS['orange']['pressure_drop_3h']:
            risk_score += 2
            risk_reasons.append(f"Significant pressure drop: {trends['pressure_drop_hpa']:.1f} hPa in 3h")
        elif trends['pressure_drop_hpa'] >= THRESHOLDS['yellow']['pressure_drop_3h']:
            risk_score += 1
            risk_reasons.append(f"Moderate pressure drop: {trends['pressure_drop_hpa']:.1f} hPa in 3h")
        
        # Factor 2: High waves
        if current['wave_height_m'] >= THRESHOLDS['red']['wave_height']:
            risk_score += 3
            risk_reasons.append(f"Extreme waves: {current['wave_height_m']:.1f} m")
        elif current['wave_height_m'] >= THRESHOLDS['orange']['wave_height']:
            risk_score += 2
            risk_reasons.append(f"High waves: {current['wave_height_m']:.1f} m")
        elif current['wave_height_m'] >= THRESHOLDS['yellow']['wave_height']:
            risk_score += 1
            risk_reasons.append(f"Elevated waves: {current['wave_height_m']:.1f} m")
        
        # Factor 3: Tide surge
        if trends['tide_rise_m'] >= 1.5:
            risk_score += 2
            risk_reasons.append(f"Rapid tide rise: {trends['tide_rise_m']:.2f} m in 3h")
        elif trends['tide_rise_m'] >= 0.8:
            risk_score += 1
            risk_reasons.append(f"Tide rising: {trends['tide_rise_m']:.2f} m in 3h")
        
        # Factor 4: Cold upwelling (surge indicator)
        if trends['temp_change_c'] <= -2.0:
            risk_score += 1
            risk_reasons.append(f"Cold upwelling detected: {trends['temp_change_c']:.1f} °C drop")
        
        # Determine alert level based on risk score
        if risk_score >= 6:
            alert_level = 'red'
            alert_message = "🚨 EMERGENCY: High risk of severe coastal flooding"
        elif risk_score >= 4:
            alert_level = 'orange'
            alert_message = "⚠️  WARNING: Significant flood risk - prepare now"
        elif risk_score >= 2:
            alert_level = 'yellow'
            alert_message = "⚡ WATCH: Elevated flood risk - monitor conditions"
        else:
            alert_level = 'green'
            alert_message = "✅ NORMAL: No immediate flood risk"
        
        assessment = {
            'level': alert_level,
            'risk_score': risk_score,
            'message': alert_message,
            'reasons': risk_reasons,
            'current_conditions': current,
            'trends': trends
        }
        
        if DEBUG:
            print(f"\n🎯 RISK ASSESSMENT:")
            print(f"   Alert Level: {alert_level.upper()}")
            print(f"   Risk Score: {risk_score}/10")
            print(f"   Message: {alert_message}")
            if risk_reasons:
                print(f"   Reasons:")
                for reason in risk_reasons:
                    print(f"      • {reason}")
        
        return assessment
    
    def _print_unified_data(self, data):
        """Pretty print the unified dataset"""
        print(f"\n🌐 UNIFIED OCEAN INTELLIGENCE:")
        print(f"   Timestamp: {data['timestamp'].strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"\n   📊 ATMOSPHERIC:")
        print(f"      Regional Pressure: {data['regional_pressure_hpa']:.1f} hPa")
        print(f"      Local Pressure: {data['local_pressure_hpa']:.1f} hPa")
        print(f"      Difference: {data['pressure_difference']:+.1f} hPa")
        print(f"      Wind: {data['wind_speed_ms']:.1f} m/s @ {data['wind_direction']:.0f}°")
        print(f"\n   🌊 OCEAN CONDITIONS:")
        print(f"      Tide Level: {data['tide_level_m']:.2f} m")
        print(f"      Water Temp: {data['water_temp_c']:.1f} °C")
        print(f"      Wave Height: {data['wave_height_m']:.2f} m")
        print(f"      Wave Period: {data['wave_period_s']:.1f} s")
        print(f"\n   ✓ Sensors: {data['sensor_status']}")


def test_data_manager():
    """Test the complete data integration system"""
    print("=" * 60)
    print("TESTING TIDEWISE DATA MANAGER")
    print("=" * 60)
    
    manager = TideWiseDataManager()
    
    # Test 1: Get current conditions (normal)
    print("\n🧪 TEST 1: Normal Conditions")
    data1 = manager.get_current_conditions()
    risk1 = manager.assess_risk_level()
    
    # Test 2: Simulate approaching storm
    print("\n\n🧪 TEST 2: Approaching Storm (Moderate)")
    manager.local_sensors.simulate_storm_conditions(storm_intensity=0.5)
    data2 = manager.get_current_conditions()
    risk2 = manager.assess_risk_level()
    
    # Test 3: Simulate severe storm
    print("\n\n🧪 TEST 3: Severe Storm")
    manager.local_sensors.simulate_storm_conditions(storm_intensity=0.9)
    data3 = manager.get_current_conditions()
    risk3 = manager.assess_risk_level()
    
    print("\n" + "=" * 60)
    print("✅ DATA MANAGER WORKING!")
    print("=" * 60)
    print("\n📋 SUMMARY:")
    print(f"   Test 1: {risk1['level'].upper()} - {risk1['message']}")
    print(f"   Test 2: {risk2['level'].upper()} - {risk2['message']}")
    print(f"   Test 3: {risk3['level'].upper()} - {risk3['message']}")
    print()
    
    return manager

if __name__ == "__main__":
    test_data_manager()
