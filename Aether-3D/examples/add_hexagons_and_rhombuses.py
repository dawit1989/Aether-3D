import json
import os
import numpy as np
from pyproj import Geod

geod = Geod(ellps="WGS84")

def hexagon_vertices(center_lat, center_lon, radius_km=25.0):
    vertices = []
    for angle in range(0, 360, 60):
        lon, lat, _ = geod.fwd(center_lon, center_lat, angle, radius_km * 1000)
        vertices.extend([float(lon), float(lat), 0.0])
    return vertices

def overlapping_rhombus_vertices(gs_lat, gs_lon, sat_lat, sat_lon, radius_km=25.0):
    mid_lat = (gs_lat + sat_lat) / 2.0
    mid_lon = (gs_lon + sat_lon) / 2.0
    fwd_az, _, _ = geod.inv(gs_lon, gs_lat, sat_lon, sat_lat)
    
    m1_lon, m1_lat, _ = geod.fwd(mid_lon, mid_lat, fwd_az + 90, radius_km * 500)
    m2_lon, m2_lat, _ = geod.fwd(mid_lon, mid_lat, fwd_az - 90, radius_km * 500)
    
    return [
        float(gs_lon), float(gs_lat), 0.0,
        float(m1_lon), float(m1_lat), 0.0,
        float(sat_lon), float(sat_lat), 0.0,
        float(m2_lon), float(m2_lat), 0.0,
    ]

def update_czml(file_path):
    print(f"Updating hexagonal footprints and rhombuses in: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    gs_lat, gs_lon = 53.110987, 8.851239
    new_packets = []

    for packet in data:
        pid = packet.get("id", "")

        # Update coverage polygons to 6-point WGS84 Hexagons
        if pid.startswith("coverage_sat_"):
            sat_num = pid.replace("coverage_sat_", "")
            # Center near GS
            sat_lat = gs_lat + (int(sat_num) * 0.15)
            sat_lon = gs_lon + (int(sat_num) * 0.15)
            hex_coords = hexagon_vertices(sat_lat, sat_lon, 25.0)

            packet["name"] = f"Satellite {sat_num} Hexagonal Beam Footprint"
            packet["polygon"] = {
                "positions": {
                    "cartographicDegrees": hex_coords,
                },
                "material": {"solidColor": {"color": {"rgba": [0, 220, 255, 80]}}},
                "outline": True,
                "outlineColor": {"rgba": [0, 220, 255, 220]},
                "perPositionHeight": True,
                "closeTop": True,
                "closeBottom": False,
            }
            new_packets.append(packet)

            # Create matching Overlapping Rhombus entity
            rhombus_coords = overlapping_rhombus_vertices(gs_lat, gs_lon, sat_lat, sat_lon, 25.0)
            rhombus_entity = {
                "id": f"overlap_rhombus_{sat_num}",
                "name": f"Overlap Rhombus (Sat {sat_num} / GS)",
                "description": f"Overlapping rhombus area between Base Station cell and Satellite {sat_num} beam footprint",
                "polygon": {
                    "positions": {
                        "cartographicDegrees": rhombus_coords,
                    },
                    "material": {"solidColor": {"color": {"rgba": [50, 205, 50, 150]}}},
                    "outline": True,
                    "outlineColor": {"rgba": [50, 255, 50, 255]},
                    "perPositionHeight": True,
                    "closeTop": True,
                    "closeBottom": False,
                }
            }
            new_packets.append(rhombus_entity)
        else:
            new_packets.append(packet)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(new_packets, f, indent=2)
    print("Done!")

if __name__ == "__main__":
    frontend_sample = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Aether3D-Frontend", "public", "sample.czml"
    )
    if os.path.exists(frontend_sample):
        update_czml(frontend_sample)
