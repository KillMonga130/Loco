#!/usr/bin/env python3
"""
Bar30 Pressure Sensor ROS Node for LoCO AUV

Reads data from BlueRobotics Bar30 depth/pressure sensor via I2C
and publishes to ROS topics.

Hardware:
- Bar30 sensor connected to Raspberry Pi I2C bus
- I2C address: 0x76 (default)

ROS Topics Published:
- /bar30/pressure (sensor_msgs/FluidPressure): Pressure in Pascals
- /bar30/temperature (std_msgs/Float32): Temperature in Celsius
- /bar30/depth (std_msgs/Float32): Depth in meters (if submerged)

Installation:
    pip3 install bluerobotics-bar30

Author: TideWise Team for LoCO AUV
License: MIT
"""

import rospy
from sensor_msgs.msg import FluidPressure, Temperature
from std_msgs.msg import Float32

# Try to import Bar30 library
try:
    from ms5837 import MS5837_30BA  # BlueRobotics Bar30 library
    BAR30_AVAILABLE = True
except ImportError:
    rospy.logwarn("Bar30 library not found. Install with: pip3 install bluerobotics-bar30")
    BAR30_AVAILABLE = False


class Bar30SensorNode:
    """
    ROS node for Bar30 pressure/temperature sensor
    """
    
    def __init__(self):
        rospy.init_node('bar30_sensor_node', anonymous=False)
        
        # Configuration
        self.publish_rate = rospy.get_param('~publish_rate', 10)  # Hz
        self.sea_level_pressure = rospy.get_param('~sea_level_pressure', 1013.25)  # hPa
        self.fluid_density = rospy.get_param('~fluid_density', 1029.0)  # kg/m³ (seawater)
        
        # Initialize sensor
        if BAR30_AVAILABLE:
            try:
                self.sensor = MS5837_30BA()
                if not self.sensor.init():
                    rospy.logerr("Failed to initialize Bar30 sensor")
                    self.sensor = None
                else:
                    # Set fluid density for depth calculation
                    self.sensor.setFluidDensity(self.fluid_density)
                    rospy.loginfo(f"Bar30 sensor initialized (fluid density: {self.fluid_density} kg/m³)")
            except Exception as e:
                rospy.logerr(f"Error initializing Bar30: {e}")
                self.sensor = None
        else:
            self.sensor = None
            rospy.logwarn("Running in simulation mode (no real sensor)")
        
        # ROS Publishers
        self.pub_pressure = rospy.Publisher('/bar30/pressure', FluidPressure, queue_size=10)
        self.pub_temperature = rospy.Publisher('/bar30/temperature', Float32, queue_size=10)
        self.pub_depth = rospy.Publisher('/bar30/depth', Float32, queue_size=10)
        
        # Timer for periodic publishing
        self.timer = rospy.Timer(rospy.Duration(1.0 / self.publish_rate), self.publish_sensor_data)
        
        rospy.loginfo(f"Bar30 node started. Publishing at {self.publish_rate} Hz")
    
    def read_sensor(self):
        """
        Read data from Bar30 sensor
        
        Returns:
            tuple: (pressure_pa, temperature_c, depth_m) or None if read fails
        """
        if self.sensor is None:
            # Simulation mode - return dummy data
            return (101325.0, 20.0, 0.0)  # 1 atm, 20°C, 0m depth
        
        try:
            if not self.sensor.read():
                rospy.logwarn("Failed to read Bar30 sensor")
                return None
            
            # Get readings
            pressure_mbar = self.sensor.pressure()  # mbar
            temperature_c = self.sensor.temperature()  # Celsius
            depth_m = self.sensor.depth()  # meters
            
            # Convert pressure to Pascals
            pressure_pa = pressure_mbar * 100.0
            
            return (pressure_pa, temperature_c, depth_m)
        
        except Exception as e:
            rospy.logerr(f"Error reading Bar30: {e}")
            return None
    
    def publish_sensor_data(self, event=None):
        """
        Read sensor and publish to ROS topics
        """
        data = self.read_sensor()
        
        if data is None:
            return
        
        pressure_pa, temperature_c, depth_m = data
        
        # Publish pressure
        pressure_msg = FluidPressure()
        pressure_msg.header.stamp = rospy.Time.now()
        pressure_msg.header.frame_id = "bar30"
        pressure_msg.fluid_pressure = pressure_pa
        self.pub_pressure.publish(pressure_msg)
        
        # Publish temperature
        temp_msg = Float32()
        temp_msg.data = temperature_c
        self.pub_temperature.publish(temp_msg)
        
        # Publish depth
        depth_msg = Float32()
        depth_msg.data = depth_m
        self.pub_depth.publish(depth_msg)
        
        # Log occasionally (every 5 seconds)
        if event is None or int(event.current_real.to_sec()) % 5 == 0:
            pressure_hpa = pressure_pa / 100.0
            rospy.logdebug(f"Bar30: {pressure_hpa:.1f} hPa, {temperature_c:.1f}°C, {depth_m:.2f}m")
    
    def run(self):
        """
        Keep node running
        """
        rospy.loginfo("Bar30 sensor node running. Press Ctrl+C to stop.")
        rospy.spin()


if __name__ == '__main__':
    try:
        node = Bar30SensorNode()
        node.run()
    except rospy.ROSInterruptException:
        rospy.loginfo("Bar30 sensor node shutting down.")
