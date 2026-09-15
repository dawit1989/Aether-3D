"""Run 3DANTS network simulation and generate a CZML visualization file."""
import importlib
import os
import sys

# Add parent directory to sys.path
_PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)

# Dynamically import module starting with a digit
_mod = importlib.import_module("examples.3D_network_with_traffic")
NetworkSimulation = _mod.NetworkSimulation
SimulationConfig = _mod.SimulationConfig

def main():
    print("Initializing 3DANTS Network Simulation...")
    output_czml = os.path.join(os.path.dirname(__file__), "generated_network.czml")
    frontend_sample_czml = os.path.join(
        _PARENT_DIR, "Aether3D-Frontend", "public", "sample.czml"
    )

    # Configure simulation run: 1 satellite pass, capped at 2000 ms for quick execution
    cfg = SimulationConfig(
        steps=1,
        max_ms=2000,
        verbose=False,
        czml_output_path=output_czml,
    )

    sim = NetworkSimulation(cfg)
    print("Running simulation layers (Geometry, Fading, Shadowing, Traffic, HAPS, BaseStation, Interference)...")
    sim.run()

    print("Simulation finished! Results:")
    print(f"  - Satellite Position points: {len(sim.results.sat_position)}")
    print(f"  - Interference entries: {len(sim.results.interference)}")
    print(f"  - CZML exported to: {output_czml}")

    # Copy generated CZML to frontend public folder
    if os.path.exists(output_czml):
        with open(output_czml, "r", encoding="utf-8") as f_in:
            czml_content = f_in.read()
        with open(frontend_sample_czml, "w", encoding="utf-8") as f_out:
            f_out.write(czml_content)
        print(f"  - Updated frontend sample dataset at: {frontend_sample_czml}")

if __name__ == "__main__":
    main()
