"""Compatibility caller for 25 fixed Wine/Ours splits of unchanged 2020 author code."""

import csv
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time
import traceback
import types
import urllib.request

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "src/paper-decision-trees-as-partitioning-machines-0f354dac486a9845a9504419e31c84c7eb39507f"


def main() -> None:
    nonce = sys.argv[1]
    assert len(nonce) == 32 and all(ch in "0123456789abcdef" for ch in nonce)
    out = HERE / "out" / f"author_result_{nonce}.json"
    assert not out.exists(), out
    csv_path = SOURCE / "experiments/results/wine/ac25/ours.csv"
    params_path = SOURCE / "experiments/results/wine/ac25/ours_exp_params.py"
    assert not csv_path.exists() and not params_path.exists()
    result = {"status": "started", "run_nonce": nonce, "cwd_initial": os.getcwd(),
              "pid_self_reported": os.getpid(), "started_ns_self_reported": time.time_ns()}
    try:
        import numpy as np
        import pandas as pd
        import scipy
        import sklearn
        import sympy

        # Compatibility adapters from the earlier Wine replay. They do not
        # implement the paper's learning or pruning algorithms.
        np.infty = np.inf
        sys.modules["python2latex"] = types.ModuleType("python2latex")
        graal = types.ModuleType("graal_utils")
        class UnusedTimer:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("Timer adapter unexpectedly called")
        graal.Timer = UnusedTimer
        sys.modules["graal_utils"] = graal
        attempted_network = []
        def deny_network(*args, **kwargs):
            attempted_network.append(True)
            raise RuntimeError("network disabled")
        urllib.request.urlopen = deny_network
        socket.socket = deny_network

        os.chdir(SOURCE)
        sys.path.insert(0, str(SOURCE / "experiments"))
        sys.path.insert(0, str(SOURCE))
        from experiments import main as author_main
        from datasets.datasets import load_datasets
        selected = list(load_datasets(["wine"]))
        assert len(selected) == 1
        data = selected[0]
        assert (data.n_examples, data.n_features, data.n_classes) == (178, 13, 3)
        author_main.launch_single_experiment(data, model_name="ours", exp_name="ac25",
                                             n_draws=25, error_prior_exponent=13.7)
        payload = csv_path.read_bytes()
        rows = list(csv.DictReader(payload.decode("utf-8").splitlines()))
        assert len(rows) == 25
        assert [int(row["draw"]) for row in rows] == list(range(25))
        assert [int(row["seed"]) for row in rows] == list(range(1, 242, 10))
        result.update({
            "status": "success", "csv_sha256": hashlib.sha256(payload).hexdigest(),
            "csv_rows": len(rows), "first_row": rows[0], "last_row": rows[-1],
            "params_sha256": hashlib.sha256(params_path.read_bytes()).hexdigest(),
            "shape": [178, 13, 3], "network_attempts_python_guard": len(attempted_network),
            "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                         "pandas": pd.__version__, "scipy": scipy.__version__,
                         "sklearn": sklearn.__version__, "sympy": sympy.__version__},
        })
    except BaseException as ex:
        result["status"] = "error"
        result["error"] = repr(ex)
        result["traceback"] = traceback.format_exc()
    result["ended_ns_self_reported"] = time.time_ns()
    with out.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
