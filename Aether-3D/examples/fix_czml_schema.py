"""Utility script to convert legacy CZML files into standard Cesium-compliant CZML."""
import json
import os
import sys

def fix_czml_packet(packet):
    if not isinstance(packet, dict):
        return packet

    # Fix position property
    if "position" in packet and isinstance(packet["position"], dict):
        pos = packet["position"]
        if "cartesian4" in pos:
            c4 = pos.pop("cartesian4")
            c = []
            # c4 was formatted as [x, y, z, t, x, y, z, t...]
            for i in range(0, len(c4), 4):
                if i + 3 < len(c4):
                    x, y, z, t = c4[i], c4[i+1], c4[i+2], c4[i+3]
                    c.extend([t, x, y, z])
            pos["cartesian"] = c
        elif "cartesian" in pos:
            # Ensure time t is first element if formatted as [x,y,z,t]
            c = pos["cartesian"]
            if len(c) >= 4 and c[0] > 1000: # X ECEF coordinate is in millions
                fixed_c = []
                for i in range(0, len(c), 4):
                    if i + 3 < len(c):
                        x, y, z, t = c[i], c[i+1], c[i+2], c[i+3]
                        fixed_c.extend([t, x, y, z])
                pos["cartesian"] = fixed_c

    # Fix coverage polygon positions
    if "polygon" in packet and isinstance(packet["polygon"], dict):
        poly = packet["polygon"]
        if "positions" in poly and isinstance(poly["positions"], dict):
            poly_pos = poly["positions"]
            poly_pos.pop("epoch", None)
            if "cartographicDegrees" in poly_pos:
                coords = poly_pos["cartographicDegrees"]
                # Strip out time offsets (like 0.0, 30.0, 60.0) that leave len % 3 != 0
                cleaned_coords = []
                idx = 0
                while idx < len(coords):
                    # Check if element at idx is a time offset (e.g. 0.0, 30.0, 60.0, 90.0, etc.)
                    # and the remaining elements can form triplets of [lon, lat, height]
                    if (len(coords) - idx) % 3 != 0:
                        idx += 1 # Skip time offset
                    else:
                        cleaned_coords.append(coords[idx])
                        idx += 1
                
                # Truncate to exact multiple of 3 if needed
                rem = len(cleaned_coords) % 3
                if rem != 0:
                    cleaned_coords = cleaned_coords[:-rem]
                
                poly_pos["cartographicDegrees"] = cleaned_coords

    return packet

def fix_czml_file(file_path):
    print(f"Fixing CZML schema in: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        fixed_data = [fix_czml_packet(p) for p in data]
    else:
        fixed_data = fix_czml_packet(data)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=2)
    print("Done!")

if __name__ == "__main__":
    frontend_sample = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Aether3D-Frontend", "public", "sample.czml"
    )
    examples_sample = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "examples", "sample.czml"
    )
    if os.path.exists(frontend_sample):
        fix_czml_file(frontend_sample)
    if os.path.exists(examples_sample):
        fix_czml_file(examples_sample)
