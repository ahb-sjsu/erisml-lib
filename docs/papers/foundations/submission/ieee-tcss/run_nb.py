"""Driver: run the notebook end-to-end as a script with shims for display()."""
from __future__ import annotations
import builtins, sys, io, os, pathlib, traceback

# Make display() a no-op
builtins.display = lambda *a, **k: None

# Force off the install branch — we have deps in this venv.
os.environ.setdefault("MPLBACKEND", "Agg")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
_orig_show = plt.show
def _noop_show(*a, **k):
    pass
plt.show = _noop_show

# Read the converted script, neutralize INSTALL_MISSING and the bad __future__ position,
# and exec inline so we keep one namespace.
SRC = pathlib.Path(__file__).with_name("tcss_public_data_analysis.py").read_text(encoding="utf-8")
SRC = SRC.replace("INSTALL_MISSING = True", "INSTALL_MISSING = False")
# Strip the orphan future import; we already have one at the top of this driver.
SRC = SRC.replace("from __future__ import annotations\n", "# from __future__ import annotations\n", 1)

ns = {"__name__": "__main__", "__file__": str(pathlib.Path(__file__).with_name("tcss_public_data_analysis.py"))}
try:
    exec(compile(SRC, "tcss_public_data_analysis.py", "exec"), ns)
except SystemExit:
    raise
except BaseException as e:
    print("\n=== EXCEPTION IN NOTEBOOK SCRIPT ===")
    traceback.print_exc()
    sys.exit(1)
print("\n=== NOTEBOOK COMPLETED ===")
