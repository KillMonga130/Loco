#!/usr/bin/env python3
"""
TideWise Web Dashboard
Real-time coastal flood risk monitoring interface
"""

from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.data_manager import TideWiseDataManager
import config

app = Flask(__name__)
data_manager = TideWiseDataManager()

# Store historical data for trend graphs
historical_data = {
    'timestamps': [],
    'pressure': [],
    'wave_height': [],
    'tide_level': [],
    'temperature': [],
    'risk_score': [],
    'alert_level': []
}

def update_historical_data(conditions, assessment):
    """Add current data to historical records (keep last 24 hours)"""
    now = datetime.now()
    
    # Add new data
    historical_data['timestamps'].append(now.isoformat())
    historical_data['pressure'].append(conditions['local_pressure_hpa'])
    historical_data['wave_height'].append(conditions['wave_height_m'])
    historical_data['tide_level'].append(conditions['tide_level_m'])
    historical_data['temperature'].append(conditions['water_temp_c'])
    historical_data['risk_score'].append(assessment['risk_score'])
    historical_data['alert_level'].append(assessment['level'])
    
    # Keep only last 24 hours of data (288 points at 5-min intervals)
    max_points = 288
    for key in historical_data:
        if len(historical_data[key]) > max_points:
            historical_data[key] = historical_data[key][-max_points:]


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html', 
                         location_name=config.LOCATION['name'],
                         latitude=config.LOCATION['latitude'],
                         longitude=config.LOCATION['longitude'])


@app.route('/api/current')
def get_current_data():
    """API endpoint for current conditions"""
    try:
        # Get latest data from manager
        conditions = data_manager.get_current_conditions()
        assessment = data_manager.assess_risk_level()
        
        # Update historical records
        update_historical_data(conditions, assessment)
        
        # Prepare response matching our HTML expectations
        response = {
            'timestamp': datetime.now().isoformat(),
            'location': {
                'name': config.LOCATION['name'],
                'latitude': config.LOCATION['latitude'],
                'longitude': config.LOCATION['longitude']
            },
            'conditions': {
                'pressure': conditions['local_pressure_hpa'],
                'wave_height': conditions['wave_height_m'],
                'tide_level': conditions['tide_level_m'],
                'temperature': conditions['water_temp_c'],
                'wind_speed': conditions['wind_speed_ms'],
                'wind_direction': conditions['wind_direction']
            },
            'trends': {
                'pressure_change': assessment['trends']['pressure_drop_hpa'] if assessment['trends'] else 0,
                'wave_change': assessment['trends']['wave_height_increase_m'] if assessment['trends'] else 0,
                'tide_change': assessment['trends']['tide_rise_m'] if assessment['trends'] else 0,
                'temp_change': assessment['trends']['temp_change_c'] if assessment['trends'] else 0
            },
            'alert': {
                'level': assessment['level'],
                'risk_score': assessment['risk_score'],
                'message': assessment['message'],
                'reasons': assessment['reasons'],
                'color': _get_alert_color(assessment['level'])
            },
            'regional_data': {
                'pressure': conditions['regional_pressure_hpa'],
                'source': 'NOAA GFS'
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/historical')
def get_historical_data():
    """API endpoint for historical trend data"""
    try:
        return jsonify(historical_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/thresholds')
def get_thresholds():
    """API endpoint for alert thresholds"""
    return jsonify({
        'yellow': {
            'pressure_drop': 3,
            'wave_height': 2.5,
            'risk_score': 2
        },
        'orange': {
            'pressure_drop': 5,
            'wave_height': 3.5,
            'risk_score': 4
        },
        'red': {
            'pressure_drop': 8,
            'wave_height': 5.0,
            'risk_score': 6
        }
    })


def _get_alert_color(level):
    """Get CSS color for alert level"""
    colors = {
        'green': '#22c55e',
        'yellow': '#eab308',
        'orange': '#f97316',
        'red': '#ef4444'
    }
    return colors.get(level.lower(), '#6b7280')


if __name__ == '__main__':
    print("=" * 60)
    print("🌊 TideWise Dashboard Starting...")
    print("=" * 60)
    print(f"📍 Location: {config.LOCATION['name']}")
    print(f"🌐 Coordinates: {config.LOCATION['latitude']}, {config.LOCATION['longitude']}")
    print(f"🔗 Dashboard: http://localhost:5000")
    print("=" * 60)
    print("\n⚡ Press Ctrl+C to stop\n")
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)
