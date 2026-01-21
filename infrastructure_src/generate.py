#!/usr/bin/env python3
"""
Traffic Data Generator for Syft Privacy Demo

This script simulates GPS traces from 100 drivers over a simulated "day of driving".
It generates realistic driving patterns including:
- Morning commute patterns (congestion)
- Workday activities
- Evening commute patterns

Each driver generates a series of (latitude, longitude, timestamp) points.
"""

import numpy as np
import pandas as pd
import time
import random
from typing import List, Tuple
import json


def simulate_driver_route(driver_id: int, start_time: pd.Timestamp) -> List[Tuple[float, float, pd.Timestamp]]:
    """
    Simulate a single driver's route for the day.

    Args:
        driver_id: Unique identifier for the driver
        start_time: When the driver's day begins

    Returns:
        List of (lat, lon, timestamp) tuples representing the driver's GPS trace
    """
    # Define key locations (simplified city layout)
    home_lat, home_lon = 40.7128 + random.uniform(-0.05, 0.05), -74.0060 + random.uniform(-0.05, 0.05)
    work_lat, work_lon = 40.7589 + random.uniform(-0.02, 0.02), -73.9851 + random.uniform(-0.02, 0.02)

    route_points = []

    # Morning commute: Home -> Work (7:00-9:00)
    morning_start = start_time.replace(hour=7, minute=0)
    commute_duration = pd.Timedelta(hours=2)  # Simulate traffic congestion

    # Generate points along the route
    num_points = 20
    for i in range(num_points):
        # Linear interpolation between home and work with some noise
        t = i / (num_points - 1)
        lat = home_lat + t * (work_lat - home_lat) + random.uniform(-0.001, 0.001)
        lon = home_lon + t * (work_lon - home_lon) + random.uniform(-0.001, 0.001)

        # Add time progression with congestion simulation
        time_offset = commute_duration * t
        # Simulate slower movement during peak hours
        if 0.3 < t < 0.7:  # Middle of commute = peak congestion
            time_offset = time_offset * 1.5  # 50% slower

        timestamp = morning_start + time_offset
        route_points.append((lat, lon, timestamp))

    # Workday: Stay at work with occasional movements (9:00-17:00)
    work_start = morning_start + commute_duration
    for hour in range(8):  # 8 hours at work
        for minute in range(0, 60, 15):  # Point every 15 minutes
            # Small movements around work area
            lat = work_lat + random.uniform(-0.005, 0.005)
            lon = work_lon + random.uniform(-0.005, 0.005)
            timestamp = work_start + pd.Timedelta(hours=hour, minutes=minute)
            route_points.append((lat, lon, timestamp))

    # Evening commute: Work -> Home (17:00-19:00)
    evening_start = work_start + pd.Timedelta(hours=8)
    evening_commute_duration = pd.Timedelta(hours=2)

    num_evening_points = 20
    for i in range(num_evening_points):
        t = i / (num_evening_points - 1)
        lat = work_lat + t * (home_lat - work_lat) + random.uniform(-0.001, 0.001)
        lon = work_lon + t * (home_lon - work_lon) + random.uniform(-0.001, 0.001)

        time_offset = evening_commute_duration * t
        # Simulate evening congestion
        if 0.2 < t < 0.8:
            time_offset = time_offset * 1.3  # 30% slower

        timestamp = evening_start + time_offset
        route_points.append((lat, lon, timestamp))

    return route_points


def generate_traffic_data(num_drivers: int = 100, simulation_days: int = 1) -> pd.DataFrame:
    """
    Generate traffic data for multiple drivers over multiple days.

    Args:
        num_drivers: Number of drivers to simulate
        simulation_days: Number of days to simulate

    Returns:
        DataFrame with columns: driver_id, latitude, longitude, timestamp
    """
    all_data = []

    print(f"🚗 Simulating traffic data for {num_drivers} drivers over {simulation_days} day(s)...")

    start_time = time.time()

    for driver_id in range(num_drivers):
        if driver_id % 20 == 0:
            print(f"  Processing driver {driver_id + 1}/{num_drivers}...")

        for day in range(simulation_days):
            day_start = pd.Timestamp('2024-01-01') + pd.Timedelta(days=day)

            # Simulate the driver's route for this day
            route_points = simulate_driver_route(driver_id, day_start)

            # Add to our dataset
            for lat, lon, timestamp in route_points:
                all_data.append({
                    'driver_id': driver_id,
                    'latitude': lat,
                    'longitude': lon,
                    'timestamp': timestamp
                })

    # Create DataFrame
    df = pd.DataFrame(all_data)

    elapsed = time.time() - start_time
    print(".2f")
    print(f"📊 Generated {len(df)} GPS points from {len(df['driver_id'].unique())} drivers")

    return df


def save_traffic_data(df: pd.DataFrame, filename: str = "traffic_data.json"):
    """
    Save the generated traffic data to a JSON file for use by other scripts.

    Args:
        df: DataFrame containing traffic data
        filename: Output filename
    """
    # Convert timestamps to strings for JSON serialization
    df_copy = df.copy()
    df_copy['timestamp'] = df_copy['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')

    # Convert to list of dicts for easy consumption by other scripts
    data_dict = {
        'drivers': df_copy.to_dict('records'),
        'metadata': {
            'num_drivers': len(df_copy['driver_id'].unique()),
            'total_points': len(df_copy),
            'date_range': {
                'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
    }

    with open(filename, 'w') as f:
        json.dump(data_dict, f, indent=2)

    print(f"💾 Traffic data saved to {filename}")
    print(f"   - {data_dict['metadata']['num_drivers']} drivers")
    print(f"   - {data_dict['metadata']['total_points']} GPS points")
    print(f"   - Time range: {data_dict['metadata']['date_range']['start']} to {data_dict['metadata']['date_range']['end']}")


if __name__ == "__main__":
    # Generate traffic data for 100 drivers over 1 day
    traffic_df = generate_traffic_data(num_drivers=100, simulation_days=1)

    # Save to file for use by upload.py
    save_traffic_data(traffic_df, "traffic_data.json")

    print("\n✅ Traffic data generation complete!")
    print("   Run 'python upload.py' to upload this data to Syft domain.")
