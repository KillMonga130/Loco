#!/usr/bin/env python3
"""
TideWise ROS Node for LoCO AUV

Integrates coastal flood prediction with LoCO hardware:
- Bar30 depth sensor for atmospheric pressure
- PixHawk IMU for wave motion estimation
- NOAA GFS data for regional weather context
- Edge AI for flood risk prediction

Publishes alerts to /tidewise/alert_level topic

Author: TideWise Team
License: MIT
"""

import rospy
from std_msgs.msg import String, Float32
from sensor_msgs.msg import FluidPressure, Imu
import sys
import os
import numpy as np
from datetime import datetime

# Add parent directory to path to import TideWise modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.noaa_gfs import NOAAGFSFetcher
from data.data_manager import TideWiseDataManager


class TideWiseROSNode:
    """
    ROS node that integrates TideWise flood prediction with LoCO sensors
    """
    
    def __init__(self):
        rospy.init_node('tidewise_node', anonymous=False)
        
        # Configuration from ROS parameters
        self.latitude = rospy.get_param('~latitude', -33.96)
        self.longitude = rospy.get_param('~longitude', 25.60)
        self.update_interval = rospy.get_param('~update_interval', 300)  # 5 minutes
        
        rospy.loginfo(f"TideWise starting for location: {self.latitude}, {self.longitude}")
        
        # Initialize TideWise data manager (using simulated sensors for now)
        self.data_manager = TideWiseDataManager(
            latitude=self.latitude,
            longitude=self.longitude
        )
        
        # Sensor data storage
        self.bar30_pressure = None  # Pascals
        self.bar30_temperature = None  # Celsius
        self.imu_accel_z_history = []  # For wave estimation
        
        # ROS Subscribers (listen to LoCO sensors)
        rospy.Subscriber('/bar30/pressure', FluidPressure, self.bar30_pressure_callback)
        rospy.Subscriber('/bar30/temperature', Float32, self.bar30_temperature_callback)
        rospy.Subscriber('/mavros/imu/data', Imu, self.imu_callback)
        
        # ROS Publishers (send TideWise predictions)
        self.pub_alert_level = rospy.Publisher('/tidewise/alert_level', String, queue_size=10)
        self.pub_risk_score = rospy.Publisher('/tidewise/risk_score', Float32, queue_size=10)
        self.pub_message = rospy.Publisher('/tidewise/message', String, queue_size=10)
        self.pub_pressure = rospy.Publisher('/tidewise/pressure_hpa', Float32, queue_size=10)
        self.pub_wave_height = rospy.Publisher('/tidewise/wave_height_m', Float32, queue_size=10)
        self.pub_surge_prob = rospy.Publisher('/tidewise/surge_probability', Float32, queue_size=10)
        
        # Timer for periodic updates
        rospy.Timer(rospy.Duration(self.update_interval), self.update_predictions)
        
        rospy.loginfo("TideWise node initialized. Publishing to /tidewise/* topics")
    
    def bar30_pressure_callback(self, msg):
        """
        Receive pressure data from Bar30 sensor
        msg.fluid_pressure is in Pascals
        """
        self.bar30_pressure = msg.fluid_pressure
        pressure_hpa = self.bar30_pressure / 100.0
        rospy.logdebug(f"Bar30 pressure: {pressure_hpa:.1f} hPa")
    
    def bar30_temperature_callback(self, msg):
        """
        Receive temperature data from Bar30 sensor
        msg.data is in Celsius
        """
        self.bar30_temperature = msg.data
        rospy.logdebug(f"Bar30 temperature: {self.bar30_temperature:.1f}°C")
    
    def imu_callback(self, msg):
        """
        Receive IMU data from PixHawk
        Extract vertical acceleration for wave motion estimation
        """
        accel_z = msg.linear_acceleration.z
        self.imu_accel_z_history.append(accel_z)
        
        # Keep last 10 seconds at ~10 Hz = 100 samples
        if len(self.imu_accel_z_history) > 100:
            self.imu_accel_z_history.pop(0)
    
    def estimate_wave_height_from_imu(self):
        """
        Estimate wave height from IMU vertical acceleration variance
        
        Physics:
        - Calm seas (0.5m waves): low acceleration variance (~0.1)
        - Moderate seas (2m waves): medium variance (~1.0)
        - Rough seas (4m waves): high variance (~5.0)
        
        Returns:
            float: Estimated wave height in meters
        """
        if len(self.imu_accel_z_history) < 10:
            return 0.8  # Default calm seas
        
        variance = np.var(self.imu_accel_z_history)
        
        # Empirical formula (needs real-ocean calibration)
        # wave_height ≈ 0.3 * sqrt(variance)
        wave_height = 0.3 * np.sqrt(variance)
        
        # Clamp to realistic range
        wave_height = max(0.1, min(wave_height, 10.0))
        
        return wave_height
    
    def update_predictions(self, event=None):
        """
        Main prediction loop - called every update_interval seconds
        
        1. Fetch NOAA data
        2. Read local sensors (Bar30, IMU)
        3. Run TideWise risk assessment
        4. Publish alerts to ROS topics
        """
        rospy.loginfo("Running TideWise prediction update...")
        
        try:
            # Get current conditions from TideWise
            assessment = self.data_manager.assess_risk_level()
            
            # Override with real sensor data if available
            if self.bar30_pressure is not None:
                local_pressure_hpa = self.bar30_pressure / 100.0
                assessment['current_conditions']['local']['pressure'] = local_pressure_hpa
                rospy.loginfo(f"Using real Bar30 pressure: {local_pressure_hpa:.1f} hPa")
            
            if len(self.imu_accel_z_history) >= 10:
                wave_height = self.estimate_wave_height_from_imu()
                assessment['current_conditions']['local']['wave_height'] = wave_height
                rospy.loginfo(f"Using IMU-estimated wave height: {wave_height:.2f} m")
            
            # Extract results
            alert_level = assessment['alert_level']
            risk_score = assessment['risk_score']
            message = assessment['message']
            
            # Get current conditions for publishing
            local = assessment['current_conditions']['local']
            pressure = local['pressure']
            wave_height = local['wave_height']
            
            # Calculate surge probability (0.0-1.0)
            surge_prob = min(risk_score / 10.0, 1.0)
            
            # Publish to ROS topics
            self.pub_alert_level.publish(alert_level)
            self.pub_risk_score.publish(risk_score)
            self.pub_message.publish(message)
            self.pub_pressure.publish(pressure)
            self.pub_wave_height.publish(wave_height)
            self.pub_surge_prob.publish(surge_prob)
            
            # Log alert
            emoji = {
                'green': '✅',
                'yellow': '⚠️',
                'orange': '🟠',
                'red': '🚨'
            }.get(alert_level, '❓')
            
            rospy.loginfo(f"{emoji} ALERT: {alert_level.upper()} (Risk: {risk_score}/10)")
            rospy.loginfo(f"   Message: {message}")
            rospy.loginfo(f"   Pressure: {pressure:.1f} hPa, Waves: {wave_height:.1f}m")
            
            # Print reasons if not green
            if alert_level != 'green' and 'reasons' in assessment:
                for reason in assessment['reasons']:
                    rospy.loginfo(f"   - {reason}")
        
        except Exception as e:
            rospy.logerr(f"Error in TideWise prediction: {e}")
            import traceback
            rospy.logerr(traceback.format_exc())
    
    def run(self):
        """
        Keep node running
        """
        rospy.loginfo("TideWise node running. Press Ctrl+C to stop.")
        rospy.spin()


if __name__ == '__main__':
    try:
        node = TideWiseROSNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("TideWise node shutting down.")
