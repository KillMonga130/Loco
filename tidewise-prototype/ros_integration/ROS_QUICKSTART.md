# TideWise ROS Integration - Quick Start

## 🚀 Installation on LoCO Raspberry Pi

### Prerequisites

Your LoCO AUV should already have:
- ✅ Ubuntu 20.04 or Raspberry Pi OS
- ✅ ROS Noetic (or Melodic)
- ✅ Bar30 sensor connected via I2C
- ✅ PixHawk with MAVROS installed

### Step 1: Install Python Dependencies

```bash
# Install required Python packages
pip3 install numpy pandas requests xarray netCDF4

# Install Bar30 sensor library (BlueRobotics)
pip3 install bluerobotics-bar30
```

### Step 2: Copy TideWise to ROS Workspace

```bash
# Navigate to your ROS workspace
cd ~/catkin_ws/src

# Create tidewise_ros package
mkdir -p tidewise_ros
cd tidewise_ros

# Copy files from this folder:
# - tidewise_node.py
# - bar30_sensor_node.py
# - tidewise.launch
# - package.xml
# - CMakeLists.txt
```

### Step 3: Build ROS Package

```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
```

### Step 4: Test Bar30 Sensor

```bash
# Make scripts executable
chmod +x ~/catkin_ws/src/tidewise_ros/bar30_sensor_node.py

# Test Bar30 sensor standalone
rosrun tidewise_ros bar30_sensor_node.py
```

You should see pressure readings like:
```
Bar30: 1012.5 hPa, 21.3°C, 0.15m
```

### Step 5: Launch TideWise

```bash
# Launch everything
roslaunch tidewise_ros tidewise.launch

# Or specify custom location (e.g., Durban)
roslaunch tidewise_ros tidewise.launch latitude:=-29.86 longitude:=31.03
```

---

## 📡 ROS Topics

### Published by TideWise

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `/tidewise/alert_level` | `std_msgs/String` | Alert level: 'green', 'yellow', 'orange', 'red' |
| `/tidewise/risk_score` | `std_msgs/Float32` | Risk score (0.0-10.0) |
| `/tidewise/message` | `std_msgs/String` | Human-readable alert message |
| `/tidewise/pressure_hpa` | `std_msgs/Float32` | Current atmospheric pressure (hPa) |
| `/tidewise/wave_height_m` | `std_msgs/Float32` | Estimated wave height (meters) |
| `/tidewise/surge_probability` | `std_msgs/Float32` | Surge probability (0.0-1.0) |

### Subscribed by TideWise

| Topic | Message Type | Description |
|-------|--------------|-------------|
| `/bar30/pressure` | `sensor_msgs/FluidPressure` | Pressure from Bar30 sensor (Pascals) |
| `/bar30/temperature` | `std_msgs/Float32` | Temperature from Bar30 (Celsius) |
| `/mavros/imu/data` | `sensor_msgs/Imu` | IMU data from PixHawk |

---

## 🧪 Testing Without Real Sensors

If you don't have Bar30/PixHawk connected yet, TideWise will use:
- **Simulated sensors** for local data
- **Real NOAA data** for regional weather

This is perfect for testing the AI model before deploying hardware!

```bash
# Test with simulated sensors
roslaunch tidewise_ros tidewise.launch
```

You'll see:
```
✅ ALERT: GREEN (Risk: 0/10)
   Message: ✅ NORMAL: No immediate flood risk
   Pressure: 1012.8 hPa, Waves: 0.8m
```

---

## 🎯 Integration with LoCO Navigation

### Example: Auto-Return to Harbor on Red Alert

Create `loco_safety_node.py`:

```python
#!/usr/bin/env python3
import rospy
from std_msgs.msg import String

def alert_callback(msg):
    alert_level = msg.data
    
    if alert_level == 'red':
        rospy.logwarn("🚨 RED ALERT - Returning to harbor!")
        # Send command to LoCO navigation
        # (Implementation depends on your LoCO setup)
        # Example: publish to /loco/command topic

rospy.init_node('loco_safety')
rospy.Subscriber('/tidewise/alert_level', String, alert_callback)
rospy.spin()
```

### Example: Data Logging for Research

```bash
# Record TideWise data for 24 hours
rosbag record -O tidewise_24h.bag /tidewise/alert_level /tidewise/risk_score /bar30/pressure
```

---

## 🔧 Configuration

Edit `config/location.yaml` to customize for your coastal area:

```yaml
location:
  name: "Kosi Bay"
  latitude: -26.88
  longitude: 32.85
  timezone: "Africa/Johannesburg"

thresholds:
  yellow:
    pressure_drop_3h: 2.5   # Lower threshold for shallow estuaries
    wave_height: 2.0
  orange:
    pressure_drop_3h: 4.0
    wave_height: 3.0
  red:
    pressure_drop_3h: 6.0
    wave_height: 4.5

# Community contacts for alerts
contacts:
  municipality: "+27 XX XXX XXXX"
  harbor_master: "+27 XX XXX XXXX"
  fisher_coop: "+27 XX XXX XXXX"
```

---

## 📊 Viewing Real-Time Data

### Option 1: Command Line

```bash
# Monitor alert level
rostopic echo /tidewise/alert_level

# Monitor risk score
rostopic echo /tidewise/risk_score

# Monitor pressure
rostopic echo /tidewise/pressure_hpa
```

### Option 2: RQT GUI

```bash
# Install RQT if not already available
sudo apt install ros-noetic-rqt ros-noetic-rqt-common-plugins

# Launch RQT
rqt
```

Then:
1. Go to **Plugins → Topics → Topic Monitor**
2. Select `/tidewise/*` topics
3. Watch real-time updates

### Option 3: Plotjuggler (Best for Graphs)

```bash
# Install
sudo apt install ros-noetic-plotjuggler-ros

# Launch
rosrun plotjuggler plotjuggler
```

Drag `/tidewise/pressure_hpa` and `/tidewise/wave_height_m` to plot trends!

---

## 🐛 Troubleshooting

### "Bar30 sensor not found"

```bash
# Check I2C connection
sudo i2cdetect -y 1

# You should see device at address 0x76
```

If not found:
- Check wiring (SDA, SCL, VCC, GND)
- Enable I2C: `sudo raspi-config` → Interfacing Options → I2C → Enable

### "Failed to fetch NOAA data"

TideWise will fall back to simulated data. Check:

```bash
# Test internet connection
ping nomads.ncep.noaa.gov

# Check Python dependencies
pip3 list | grep xarray
```

### "No IMU data from PixHawk"

Check MAVROS is running:

```bash
rostopic list | grep mavros

# Should see /mavros/imu/data
```

If not, launch MAVROS:

```bash
roslaunch mavros px4.launch fcu_url:=/dev/ttyACM0:57600
```

---

## 🎓 Educational Use

### For Ocean Hub Workshops

**Activity 1: Understanding Pressure**
```bash
# Students watch pressure drop in real-time
rostopic echo /bar30/pressure

# Blow gently on Bar30 sensor
# Pressure increases slightly (demonstrates sensitivity)
```

**Activity 2: Storm Simulation**
```python
# Modify tidewise_node.py to simulate storm
# Students see how AI responds to changing conditions
```

**Activity 3: Business Case**
- Deploy LoCO near harbor entrance
- Collect 1 week of data
- Calculate: "How much warning time do we get?"
- Present to municipality: "R40k/year subscription = R2M damage prevented"

---

## 📞 Support

**Questions?**
- WhatsApp: [LoCO AUV Mzansi](https://chat.whatsapp.com/LUfKavtwcHDFeLoBMZHRB4)
- Email: alexis@oceanhub.africa (Ocean Hub)
- GitHub Issues: (create repo)

**Want to contribute?**
TideWise is open-source! Improvements welcome:
- Better wave height estimation from IMU
- Machine learning model training
- SMS/WhatsApp alert integration
- Dashboard web app

---

## 🌊 Next Steps

1. ✅ Get TideWise running with simulated sensors
2. ⬜ Connect real Bar30 sensor
3. ⬜ Calibrate wave height estimation in real ocean
4. ⬜ Deploy near coastal area for 1 month
5. ⬜ Tune alert thresholds based on local conditions
6. ⬜ Present results at LoCO community meetup
7. ⬜ Pitch to municipality for subscription

**Let's build coastal resilience together!** 🤖🌊
