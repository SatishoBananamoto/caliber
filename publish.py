#!/usr/bin/env python3
"""Publish caliber to PyPI.

Usage:
    kv run -e pypi -- python3 publish.py    # Uses PYPI_TOKEN from kv
    PYPI_TOKEN=xxx python3 publish.py       # Manual token
"""
import os
import sys

token = os.environ.get("PYPI_TOKEN")
if not token:
    print("Error: PYPI_TOKEN not set")
    print("Usage: kv run -e pypi -- python3 publish.py")
    sys.exit(1)

# Write temporary .pypirc
import tempfile
pypirc = tempfile.NamedTemporaryFile(mode='w', suffix='.pypirc', delete=False)
pypirc.write(f"""[pypi]
username = __token__
password = {token}
""")
pypirc.close()

import subprocess
result = subprocess.run(
    ["python3", "-m", "twine", "upload",
     "--config-file", pypirc.name,
     "dist/*"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
)

os.unlink(pypirc.name)
sys.exit(result.returncode)
