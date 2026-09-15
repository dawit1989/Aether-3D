"""Utility script to convert legacy cartesian4 positions into standard CZML cartesian positions."""
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

    # Fix coverage polygon positions if needed
    if "polygon" in packet and isinstance(packet["polygon"], dict):
        poly = packet["polygon"]
        if "positions" in poly and isinstance(poly["positions"], dict):
            poly_pos = poly["positions"]
            if "cartographicDegrees" in poly_pos and "epoch" in poly_pos:
                # Remove epoch if cartographicDegrees is a flat 3D coordinates array
                poly_pos.pop("epoch", None)

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
