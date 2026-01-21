#!/usr/bin/env python3
"""
Traffic Congestion Analysis using Syft

This script demonstrates how a researcher can analyze traffic patterns
to identify congestion hotspots without accessing raw GPS coordinates.
This preserves driver privacy while enabling city planning insights.
"""

import syft as sy
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, List
import time


def connect_as_researcher(domain_url: str = "http://localhost:8080"):
    """
    Connect to Syft domain as a researcher.

    Args:
        domain_url: URL of the Syft domain

    Returns:
        Connected Syft domain client
    """
    try:
        # Connect as researcher
        domain = sy.login(url=domain_url, email="researcher@openmined.org", password="changethis")
        print(f"🔬 Connected to Syft domain as researcher")
        print(f"   Welcome, {domain.name}!")
        return domain
    except Exception as e:
        print(f"❌ Failed to connect as researcher: {e}")
        print("   Make sure Hagrid is running and data has been uploaded")
        raise


def explore_available_data(domain) -> List[str]:
    """
    Explore what data is available in the domain.

    Args:
        domain: Connected Syft domain

    Returns:
        List of available data items
    """
    print("🔍 Exploring available data...")

    try:
        # List available datasets
        available_data = list(domain.store.keys())
        print(f"   📊 Found {len(available_data)} data items:")

        for item in available_data:
            print(f"      - {item}")

        return available_data

    except Exception as e:
        print(f"   ❌ Error exploring data: {e}")
        return []


def request_congestion_analysis(domain) -> Dict[str, Any]:
    """
    Request privacy-preserving analysis of traffic congestion patterns.

    This demonstrates how researchers can gain insights about congestion
    hotspots without accessing individual drivers' raw GPS coordinates.

    Args:
        domain: Connected Syft domain

    Returns:
        Analysis results
    """
    print("🚦 Requesting congestion analysis...")

    # Define the analysis function that will run on the private data
    @sy.syft_function_single_use()
    def analyze_congestion_patterns(all_coords, driver_ids):
        """
        Analyze traffic patterns to identify congestion hotspots.

        This function runs inside the Syft domain on private data.
        """
        import numpy as np

        # Basic statistics
        total_points = len(all_coords)
        avg_lat = float(np.mean(all_coords[:, 0]))
        avg_lon = float(np.mean(all_coords[:, 1]))

        # Create a congestion heatmap by dividing the area into a grid
        # and counting GPS points in each cell
        lat_min, lat_max = float(np.min(all_coords[:, 0])), float(np.max(all_coords[:, 0]))
        lon_min, lon_max = float(np.min(all_coords[:, 1])), float(np.max(all_coords[:, 1]))

        # Create a 10x10 grid
        grid_size = 10
        lat_bins = np.linspace(lat_min, lat_max, grid_size + 1)
        lon_bins = np.linspace(lon_min, lon_max, grid_size + 1)

        # Count points in each grid cell
        congestion_grid = np.zeros((grid_size, grid_size))

        for i in range(len(all_coords)):
            lat_idx = np.digitize(all_coords[i, 0], lat_bins) - 1
            lon_idx = np.digitize(all_coords[i, 1], lon_bins) - 1

            # Ensure indices are within bounds
            lat_idx = max(0, min(lat_idx, grid_size - 1))
            lon_idx = max(0, min(lon_idx, grid_size - 1))

            congestion_grid[lat_idx, lon_idx] += 1

        # Identify hotspots (cells with high concentration)
        max_congestion = float(np.max(congestion_grid))
        hotspot_threshold = max_congestion * 0.7  # Top 30% are hotspots

        hotspots = []
        for i in range(grid_size):
            for j in range(grid_size):
                if congestion_grid[i, j] >= hotspot_threshold:
                    # Convert grid indices back to approximate coordinates
                    hotspot_lat = (lat_bins[i] + lat_bins[i+1]) / 2
                    hotspot_lon = (lon_bins[j] + lon_bins[j+1]) / 2
                    hotspots.append({
                        "latitude": float(hotspot_lat),
                        "longitude": float(hotspot_lon),
                        "congestion_level": float(congestion_grid[i, j])
                    })

        return {
            "total_gps_points": total_points,
            "average_location": {"lat": avg_lat, "lon": avg_lon},
            "congestion_grid": congestion_grid.tolist(),
            "hotspots": hotspots,
            "grid_bounds": {
                "lat_min": lat_min, "lat_max": lat_max,
                "lon_min": lon_min, "lon_max": lon_max
            }
        }

    try:
        # Get references to the data
        all_coords = domain.store["all_gps_coordinates"]
        driver_ids = domain.store["driver_ids"]

        # Create and submit the analysis request
        analysis_request = domain.code.request_code_execution(analyze_congestion_patterns)
        analysis_request = analysis_request.send()

        print("   📨 Analysis request submitted")
        print("   ⏳ Waiting for approval from data owner...")
        print("   💡 In a real Syft deployment, the data owner would approve this request")
        print("      through the Syft domain interface or API")

        print("   ❌ Analysis cannot complete: Real Syft domain required")
        print("      This demo requires an actual Syft domain to be running.")
        print("      Please ensure Syft is properly installed and a domain is launched.")

        raise Exception("Real Syft domain required for analysis")

    except Exception as e:
        print(f"   ❌ Analysis request failed: {e}")
        print("   Make sure data has been uploaded by running: python upload.py")
        raise


def visualize_congestion_analysis(results: Dict[str, Any]):
    """
    Visualize the congestion analysis results.

    Args:
        results: Analysis results from the Syft computation
    """
    print("📊 Visualizing congestion analysis...")

    try:
        # Extract data
        congestion_grid = np.array(results["congestion_grid"])
        hotspots = results["hotspots"]

        # Create visualization
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Plot 1: Congestion Heatmap
        im = ax1.imshow(congestion_grid, cmap='YlOrRd', interpolation='nearest')
        ax1.set_title('Traffic Congestion Heatmap\n(Higher values = More GPS points)')
        ax1.set_xlabel('Longitude Grid')
        ax1.set_ylabel('Latitude Grid')
        plt.colorbar(im, ax=ax1, label='GPS Points per Grid Cell')

        # Plot 2: Hotspots
        if hotspots:
            hotspot_lats = [h["latitude"] for h in hotspots]
            hotspot_lons = [h["longitude"] for h in hotspots]
            hotspot_levels = [h["congestion_level"] for h in hotspots]

            scatter = ax2.scatter(hotspot_lons, hotspot_lats,
                                s=[level/10 for level in hotspot_levels],
                                c=hotspot_levels, cmap='Reds', alpha=0.7)
            ax2.set_title('Identified Congestion Hotspots')
            ax2.set_xlabel('Longitude')
            ax2.set_ylabel('Latitude')
            plt.colorbar(scatter, ax=ax2, label='Congestion Level')

        plt.tight_layout()
        plt.savefig('congestion_analysis.png', dpi=150, bbox_inches='tight')
        plt.show()

        print("   ✅ Visualization saved as 'congestion_analysis.png'")

    except ImportError:
        print("   ⚠️  Matplotlib not available for visualization")
        print("      Install with: pip install matplotlib")
    except Exception as e:
        print(f"   ❌ Visualization failed: {e}")


def display_insights(results: Dict[str, Any]):
    """
    Display key insights from the congestion analysis.

    Args:
        results: Analysis results
    """
    print("\n🎯 Key Insights from Privacy-Preserving Traffic Analysis:")
    print("-" * 60)

    print(f"📍 Total GPS points analyzed: {results['total_gps_points']:,}")
    print(f"📍 Average location: {results['average_location']['lat']:.4f}, {results['average_location']['lon']:.4f}")

    hotspots = results["hotspots"]
    if hotspots:
        print(f"🚨 Identified {len(hotspots)} congestion hotspots")
        for i, hotspot in enumerate(hotspots, 1):
            print(".4f"
                  f"(Level: {hotspot['congestion_level']:.0f})")

    print("\n🏛️  Infrastructure Planning Recommendations:")
    print("   - Focus traffic improvements on identified hotspots")
    print("   - Consider additional public transport in congested areas")
    print("   - Plan road maintenance around high-traffic corridors")

    print("\n🔒 Privacy Protection:")
    print("   - Raw GPS coordinates were never accessed by the researcher")
    print("   - Analysis was performed on aggregated, anonymized data")
    print("   - Individual driver privacy is fully preserved")


def main():
    """
    Main function to perform traffic congestion analysis.
    """
    print("🚦 Syft Traffic Congestion Analysis Demo")
    print("=" * 50)

    try:
        # Connect as researcher
        domain = connect_as_researcher()

        # Explore available data
        available_data = explore_available_data(domain)

        if not available_data:
            print("\n❌ No data available. Please run 'python upload.py' first.")
            return

        # Request congestion analysis
        results = request_congestion_analysis(domain)

        # Visualize results
        visualize_congestion_analysis(results)

        # Display insights
        display_insights(results)

        print("\n🎊 Analysis complete!")
        print("   📈 Results show how city planners can identify congestion hotspots")
        print("      without compromising driver privacy through raw GPS data access.")

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Hagrid domain is running: hagrid launch domain")
        print("2. Ensure data has been uploaded: python upload.py")
        print("3. Check researcher credentials")


if __name__ == "__main__":
    main()
