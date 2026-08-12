"""Makes `rewritten_models` and `idempotence_tests` importable as top-level
packages regardless of where pytest is invoked from or how it resolves
rootdir — both live directly under this directory, as siblings."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
