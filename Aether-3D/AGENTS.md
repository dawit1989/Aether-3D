# Repository Guidelines

## Project Structure & Module Organization

```
Aether-3D/
|-- 3DANTS/  # Python package
|   |-- analysis/
|   |-- communication_channel/
|   |-- position_and_mobility/
|   |-- Traffic/
|   |-- __init__.py
|-- docs/
|-- tests/
|-- examples/
|-- README.md
```

The project is named Aether-3D (formerly 3DANTS). The Python package
directory is named `3DANTS` (starts with a digit), so it cannot be
imported with a plain `import` statement. Use `importlib.import_module` instead.

## Build, Test, and Development Commands

```bash
# Install dependencies

# Run all tests
python3 -m pytest tests/ -v

# Run a specific test file
python3 -m pytest tests/test_3gpp_numerical.py -v

# Run a single test class
python3 -m pytest tests/test_simulation.py::TestNetworkSimulationLayers -v

# Run an example
python3 examples/3D_network_with_traffic.py
```

## Coding Style & Naming Conventions

- Language: Python 3.12+
- Indentation: 4 spaces
- Encoding: UTF-8 (no BOM)
- snake_case for functions/variables, PascalCase for classes

## Testing Guidelines

- Framework: `unittest.TestCase` classes, executed via pytest
- File naming: `test_<module>.py`
- Run: `python3 -m pytest tests/ -v`

## Commit & Pull Request Guidelines

- Write clear, descriptive commit messages
- Include test results in comments
