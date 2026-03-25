#!/usr/bin/env python3
"""
PySyft Traffic Privacy Demo Server
Connects the terminal (backend computation) with the interactive HTML (frontend).

Run: python demo_server.py
Then open: http://localhost:8000
"""

import asyncio
import json
import time
import numpy as np
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

app = FastAPI()

# --- Data Generation ---
NYC_CENTER = {"lat": 40.7128, "lon": -74.0060}
SPREAD = 0.003  # Congested scenario

drivers_data = []
for driver_id in range(5):
    points = []
    for point_idx in range(3):
        lat = NYC_CENTER["lat"] + (np.random.random() - 0.5) * SPREAD
        lon = NYC_CENTER["lon"] + (np.random.random() - 0.5) * SPREAD
        points.append({"lat": round(lat, 6), "lon": round(lon, 6)})
    drivers_data.append({"id": driver_id, "points": points})


def print_banner():
    print()
    print("=" * 60)
    print("  PySyft Traffic Privacy Demo Server")
    print("  Independent demo by Luis Minvielle for OpenMined")
    print("=" * 60)
    print()
    print(f"  Datasite:  NYC Traffic Analysis")
    print(f"  Drivers:   {len(drivers_data)} drivers, {len(drivers_data) * 3} GPS records")
    print(f"  Status:    Ready")
    print()
    print("  Open in browser: http://localhost:8000")
    print("  Press Ctrl+C to stop")
    print()
    print("-" * 60)
    print()


# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def serve_html():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.get("/api/drivers")
async def get_drivers():
    return {"drivers": drivers_data}


@app.get("/api/analyze")
async def analyze(mode: str = "safe"):
    """Stream the analysis steps as Server-Sent Events."""

    async def event_stream():
        if mode == "unsafe":
            yield sse("step", "$ analyze_traffic(raw_gps_data)")
            print("\n[REQUEST] Analyze WITHOUT Privacy")
            print("  Mode: Direct data transmission (UNSAFE)")

            await asyncio.sleep(0.4)
            yield sse("info", "Connecting to central server...")
            print("  Connecting to central server...")

            await asyncio.sleep(0.6)
            yield sse("warn", "⚠ WARNING: Sending raw GPS coordinates to server")
            print("  ⚠ WARNING: Sending raw GPS in plaintext")

            await asyncio.sleep(0.3)
            yield sse("blank", "")

            # Expose each driver's data
            for d in drivers_data:
                p = d["points"][0]
                msg = f"🚨 EXPOSED Driver {d['id']}: lat={p['lat']}, lon={p['lon']}"
                yield sse("data-leak", json.dumps({
                    "driver_id": d["id"],
                    "lat": p["lat"],
                    "lon": p["lon"],
                    "message": msg,
                }))
                print(f"  🚨 LEAKED → Driver {d['id']}: ({p['lat']}, {p['lon']})")
                await asyncio.sleep(0.3)

            await asyncio.sleep(0.2)
            yield sse("blank", "")
            yield sse("warn", "🚨 All 15 GPS records transmitted in plaintext")
            yield sse("warn", "🚨 Any interceptor can see exact driver locations")
            yield sse("warn", "🚨 Data permanently exposed. Cannot be recalled")
            print("  🚨 All records exposed. Privacy: NONE")

            await asyncio.sleep(0.4)
            yield sse("blank", "")

            # Compute result
            all_lats = [p["lat"] for d in drivers_data for p in d["points"]]
            lat_std = np.std(all_lats)
            level = "HIGH (Congestion Detected)" if lat_std < 0.005 else "LOW (Free Flow)"

            yield sse("info", "Computing traffic density...")
            await asyncio.sleep(0.4)
            yield sse("step", f"Result: TRAFFIC LEVEL = {level}")
            print(f"  Result: {level}")

            await asyncio.sleep(0.2)
            yield sse("result-danger", f"⚠ Correct result, but ALL driver locations are now exposed. Privacy: NONE")
            print(f"  Privacy: NONE\n")

        else:
            yield sse("step", '$ syft.login(url="datasite.local")')
            print("\n[REQUEST] Analyze WITH PySyft")
            print("  Mode: Privacy-preserving computation")

            await asyncio.sleep(0.4)
            yield sse("ok", "✓ Connected to NYC Traffic Datasite")
            print("  ✓ Connected to Datasite")

            await asyncio.sleep(0.3)
            yield sse("blank", "")

            yield sse("step", "$ client.code.request_code_execution(analyze_traffic)")
            await asyncio.sleep(0.4)
            yield sse("shield", "🔒 Code request submitted for review")
            print("  🔒 Code request submitted")

            await asyncio.sleep(0.3)
            yield sse("info", "   Researcher CANNOT see the data")
            yield sse("info", "   Only the function definition is sent")
            print("  → Researcher cannot see data")

            await asyncio.sleep(0.3)
            yield sse("blank", "")

            yield sse("shield", "👀 Data Owner reviewing code...")
            print("  👀 Data Owner reviewing code...")
            await asyncio.sleep(0.4)
            yield sse("info", "   def analyze_traffic(coords):")
            await asyncio.sleep(0.15)
            yield sse("info", "       lat_std = coords[:, 0].std()")
            await asyncio.sleep(0.15)
            yield sse("info", '       return "HIGH" if lat_std < 0.005 else "FREE"')

            await asyncio.sleep(0.3)
            yield sse("blank", "")

            yield sse("ok", "✓ APPROVED by Data Owner")
            print("  ✓ Approved by Data Owner")

            await asyncio.sleep(0.4)
            yield sse("shield", "⚡ Executing on private data (locally)...")
            print("  ⚡ Executing computation locally...")

            for d in drivers_data:
                yield sse("encrypted", json.dumps({
                    "driver_id": d["id"],
                    "message": f"🔒 Driver {d['id']}: [ENCRYPTED] processing locally...",
                }))
                print(f"  🔒 Driver {d['id']}: processed locally (encrypted)")
                await asyncio.sleep(0.2)

            await asyncio.sleep(0.3)
            yield sse("blank", "")

            # Compute result
            all_lats = [p["lat"] for d in drivers_data for p in d["points"]]
            lat_std = np.std(all_lats)
            level = "HIGH (Congestion Detected)" if lat_std < 0.005 else "LOW (Free Flow)"

            yield sse("ok", "✓ Computation complete")
            yield sse("step", f"Result: TRAFFIC LEVEL = {level}")
            print(f"  ✓ Result: {level}")

            await asyncio.sleep(0.2)
            yield sse("ok", "🔒 Raw GPS data NEVER left the Datasite")
            yield sse("ok", "🔒 Only the aggregate result was returned")

            yield sse("result-success", f"🔒 Same result. Zero data exposure. Privacy: FULL (Structured Transparency)")
            print(f"  🔒 Privacy: FULL")
            print(f"  Data never left the Datasite.\n")

        yield sse("done", "")

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def sse(event: str, data: str) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {data}\n\n"


if __name__ == "__main__":
    print_banner()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
