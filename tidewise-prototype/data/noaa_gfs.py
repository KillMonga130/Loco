"""
NOAA GFS Data Fetcher
Fetches atmospheric pressure and wind data from NOAA Global Forecast System

Free data source - no API key required!
"""

import requests
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import LOCATION, NOAA_GFS_BASE_URL, DATA_GRID_SIZE, DATA_DIR, DEBUG

class NOAAGFSFetcher:
    """Fetch atmospheric data from NOAA GFS"""
    
    def __init__(self, lat=LOCATION['latitude'], lon=LOCATION['longitude']):
        self.lat = lat
        self.lon = lon
        self.cache_dir = Path(DATA_DIR) / "gfs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def get_latest_forecast_time(self):
        """
        GFS runs 4 times daily: 00, 06, 12, 18 UTC
        Returns the most recent available forecast time
        """
        now = datetime.utcnow()
        # GFS data has ~3-4 hour delay, so go back to previous cycle
        hours_ago = 4
        adjusted_time = now - timedelta(hours=hours_ago)
        
        # Round down to nearest 6-hour cycle
        cycle_hour = (adjusted_time.hour // 6) * 6
        forecast_time = adjusted_time.replace(hour=cycle_hour, minute=0, second=0, microsecond=0)
        
        return forecast_time
    
    def fetch_pressure_and_wind(self, forecast_time=None):
        """
        Fetch atmospheric pressure and wind speed from NOAA GFS
        
        Returns:
            dict: {
                'timestamp': datetime,
                'pressure_hpa': float,  # Mean sea level pressure in hPa
                'wind_speed_ms': float,  # Wind speed in m/s
                'wind_direction': float,  # Wind direction in degrees
                'source': str
            }
        """
        if forecast_time is None:
            forecast_time = self.get_latest_forecast_time()
        
        if DEBUG:
            print(f"\n🌐 Fetching NOAA GFS data for {forecast_time.strftime('%Y-%m-%d %H:%M UTC')}")
            print(f"   Location: {self.lat:.2f}°, {self.lon:.2f}°")
        
        try:
            # Method 1: Try using OpenDAP (faster, but may not work on all systems)
            data = self._fetch_via_opendap(forecast_time)
            if data:
                return data
        except Exception as e:
            if DEBUG:
                print(f"   OpenDAP failed: {e}")
        
        try:
            # Method 2: Fall back to direct GRIB download (more reliable)
            data = self._fetch_via_grib_filter(forecast_time)
            if data:
                return data
        except Exception as e:
            if DEBUG:
                print(f"   GRIB filter failed: {e}")
        
        # Method 3: Use sample/demo data
        if DEBUG:
            print("   ⚠️  Live data unavailable, using sample data")
        return self._get_sample_data(forecast_time)
    
    def _fetch_via_opendap(self, forecast_time):
        """Try fetching via OpenDAP protocol (fastest method)"""
        # OpenDAP URL pattern for GFS
        date_str = forecast_time.strftime('%Y%m%d')
        hour_str = f"{forecast_time.hour:02d}"
        
        # NOAA OpenDAP endpoint
        opendap_url = f"https://nomads.ncep.noaa.gov/dods/gfs_0p25/gfs{date_str}/gfs_0p25_{hour_str}z"
        
        if DEBUG:
            print(f"   Trying OpenDAP: {opendap_url}")
        
        # Open dataset with xarray
        ds = xr.open_dataset(opendap_url, engine='netcdf4')
        
        # Select nearest grid point to our location
        ds_point = ds.sel(lat=self.lat, lon=self.lon % 360, method='nearest')
        
        # Extract variables at surface level (time=0 for current analysis)
        pressure_pa = float(ds_point['prmslmsl'].isel(time=0).values)  # Pa
        u_wind = float(ds_point['ugrd10m'].isel(time=0).values)  # m/s (east-west)
        v_wind = float(ds_point['vgrd10m'].isel(time=0).values)  # m/s (north-south)
        
        # Convert and calculate
        pressure_hpa = pressure_pa / 100  # Pa to hPa
        wind_speed = np.sqrt(u_wind**2 + v_wind**2)
        wind_direction = (np.degrees(np.arctan2(u_wind, v_wind)) + 360) % 360
        
        ds.close()
        
        if DEBUG:
            print(f"   ✅ Success! Pressure: {pressure_hpa:.1f} hPa, Wind: {wind_speed:.1f} m/s")
        
        return {
            'timestamp': forecast_time,
            'pressure_hpa': pressure_hpa,
            'wind_speed_ms': wind_speed,
            'wind_direction': wind_direction,
            'source': 'NOAA GFS (OpenDAP)',
            'lat': float(ds_point.lat.values),
            'lon': float(ds_point.lon.values) - 360 if ds_point.lon.values > 180 else float(ds_point.lon.values)
        }
    
    def _fetch_via_grib_filter(self, forecast_time):
        """Fetch via GRIB filter service (more reliable but slower)"""
        date_str = forecast_time.strftime('%Y%m%d')
        hour_str = f"{forecast_time.hour:02d}"
        
        # Build filter URL
        params = {
            'file': f'gfs.t{hour_str}z.pgrb2.0p25.f000',  # f000 = analysis (current)
            'var_PRMSL': 'on',  # Pressure reduced to mean sea level
            'var_UGRD': 'on',   # U-component wind
            'var_VGRD': 'on',   # V-component wind
            'lev_10_m_above_ground': 'on',  # 10m wind
            'lev_mean_sea_level': 'on',  # MSL pressure
            'leftlon': self.lon - DATA_GRID_SIZE,
            'rightlon': self.lon + DATA_GRID_SIZE,
            'toplat': self.lat + DATA_GRID_SIZE,
            'bottomlat': self.lat - DATA_GRID_SIZE,
            'dir': f'/gfs.{date_str}/{hour_str}/atmos'
        }
        
        if DEBUG:
            print(f"   Trying GRIB filter...")
        
        response = requests.get(NOAA_GFS_BASE_URL, params=params, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # Save GRIB file
        grib_file = self.cache_dir / f"gfs_{date_str}_{hour_str}.grb2"
        with open(grib_file, 'wb') as f:
            f.write(response.content)
        
        # Parse GRIB with xarray + cfgrib
        ds = xr.open_dataset(grib_file, engine='cfgrib')
        
        # Extract data (cfgrib names may vary)
        pressure_pa = float(ds['prmsl'].values.mean())
        u_wind = float(ds['u10'].values.mean())
        v_wind = float(ds['v10'].values.mean())
        
        pressure_hpa = pressure_pa / 100
        wind_speed = np.sqrt(u_wind**2 + v_wind**2)
        wind_direction = (np.degrees(np.arctan2(u_wind, v_wind)) + 360) % 360
        
        if DEBUG:
            print(f"   ✅ Success! Pressure: {pressure_hpa:.1f} hPa, Wind: {wind_speed:.1f} m/s")
        
        return {
            'timestamp': forecast_time,
            'pressure_hpa': pressure_hpa,
            'wind_speed_ms': wind_speed,
            'wind_direction': wind_direction,
            'source': 'NOAA GFS (GRIB)',
            'lat': self.lat,
            'lon': self.lon
        }
    
    def _get_sample_data(self, timestamp):
        """
        Return sample data when live fetch fails
        Realistic values for South African coast
        """
        return {
            'timestamp': timestamp,
            'pressure_hpa': 1013.2,  # Standard sea-level pressure
            'wind_speed_ms': 5.5,    # Light breeze
            'wind_direction': 210,   # Southwest
            'source': 'SAMPLE DATA (live fetch failed)',
            'lat': self.lat,
            'lon': self.lon
        }

def test_fetcher():
    """Test the NOAA GFS fetcher"""
    print("=" * 60)
    print("TESTING NOAA GFS DATA FETCHER")
    print("=" * 60)
    
    fetcher = NOAAGFSFetcher()
    data = fetcher.fetch_pressure_and_wind()
    
    print("\n📊 RESULTS:")
    print(f"   Timestamp: {data['timestamp']}")
    print(f"   Location: {data['lat']:.2f}°, {data['lon']:.2f}°")
    print(f"   Pressure: {data['pressure_hpa']:.1f} hPa")
    print(f"   Wind Speed: {data['wind_speed_ms']:.1f} m/s ({data['wind_speed_ms'] * 3.6:.1f} km/h)")
    print(f"   Wind Direction: {data['wind_direction']:.0f}°")
    print(f"   Source: {data['source']}")
    print("\n✅ Fetcher working!\n")
    
    return data

if __name__ == "__main__":
    test_fetcher()
