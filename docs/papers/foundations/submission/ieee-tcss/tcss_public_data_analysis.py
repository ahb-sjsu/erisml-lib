#!/usr/bin/env python
# coding: utf-8

# # TCSS public-data revision analysis notebook
# 
# This notebook is designed for the IEEE TCSS major revision of **"Geometric Prediction of Economic Behavior: Cross-Domain Validation Across Game Theory and Prospect Theory."**
# 
# It does four things:
# 
# 1. Downloads public datasets from their source repositories.
# 2. Recomputes individual-level or item-level behavioral summaries with uncertainty intervals.
# 3. Compares the paper's frozen geometric predictions against public-data estimates where the item mapping is available.
# 4. Runs reviewer-facing robustness checks: bootstrap intervals, country-level heterogeneity, public-goods trajectories, and a high-stakes ultimatum boundary-condition test.
# 
# The notebook deliberately separates **data/statistical validation** from the **frozen geometric encoding layer**. For the manuscript, that separation is important: the reviewer concern is not just whether the model can fit a few aggregate targets, but whether a frozen specification survives public, individual-level data.

# ## Public sources used
# 
# The notebook attempts to download the following sources:
# 
# - **Ruggeri et al. (2020), prospect-theory replication**: OSF project `esxc4` from the Nature Human Behaviour data-availability statement, with an OpenCogData mirror fallback. This is the reviewer-priority dataset for the prospect-theory extension.
# - **Fraser and Nettle (2020), hunger and social decisions**: Zenodo record 3764693, including Experiment_1.csv, Experiment_2.csv, Experiment_2_time.csv, and the original R analysis script.
# - **Andersen et al. (2011), Stakes Matter in Ultimatum Games**: openICPSR project 112485. This is optional because openICPSR sometimes requires accepting terms or logging in before download. If the automatic download fails, the notebook tells you where to place the manually downloaded `.dta` file.
# 
# No data are bundled with this notebook.

# In[ ]:


# Optional one-time dependency installer.
# Set INSTALL_MISSING = False if you are running in a locked-down environment.
INSTALL_MISSING = True

import importlib.util
import subprocess
import sys

REQUIRED_PACKAGES = {
    "requests": "requests",
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "statsmodels": "statsmodels",
    "matplotlib": "matplotlib",
    "openpyxl": "openpyxl",
    "pyarrow": "pyarrow",
    "pyreadstat": "pyreadstat",
    "pyreadr": "pyreadr",
    "tqdm": "tqdm",
}

missing = [pip_name for module_name, pip_name in REQUIRED_PACKAGES.items()
           if importlib.util.find_spec(module_name) is None]

if missing and INSTALL_MISSING:
    print("Installing missing packages:", missing)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *missing])
elif missing:
    print("Missing packages. Install them before running the analysis:", missing)
else:
    print("All required packages are already available.")


# In[ ]:


from __future__ import annotations

import json
import math
import os
import re
import shutil
import textwrap
import time
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote, unquote

import numpy as np
import pandas as pd
import requests
from scipy.stats import norm, chi2
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 160)

PROJECT_DIR = Path("tcss_public_data_analysis").resolve()
RAW_DIR = PROJECT_DIR / "data_raw"
INTERIM_DIR = PROJECT_DIR / "data_interim"
OUT_DIR = PROJECT_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

for d in [PROJECT_DIR, RAW_DIR, INTERIM_DIR, OUT_DIR, FIG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print(f"Project directory: {PROJECT_DIR}")


# ## Configuration
# 
# Adjust the few values below before a final manuscript run.
# 
# The `RUGGERI_MANUAL_MAP` is intentionally exposed. Public OSF exports sometimes use different variable names depending on whether the CSV, feather, or SPSS file is used. The automatic mapper tries common aliases such as `P1`, `Q1`, `Problem1`, and `KT1`, but you should verify item mappings against the survey instrument before using final numbers in the paper.

# In[ ]:


# Dataset identifiers and download configuration
ZENODO_FRASER_NETTLE_RECORD_ID = "3764693"

# Nature Human Behaviour data/code availability points to OSF short ID esxc4.
# The OpenCogData mirror has also used OSF short ID vwj2k.
# The downloader tries both and recursively traverses child components.
RUGGERI_OSF_IDS = ["esxc4", "vwj2k"]

OPENICPSR_PROJECT_ID = "112485"
OPENICPSR_DTA_FILENAME = "20100982_DATA.dta"

# Game endowment assumptions used only to convert token amounts to percentages.
# Change these after inspecting the dataset codebook if necessary.
ULTIMATUM_ENDOWMENT = 10.0
PUBLIC_GOODS_ENDOWMENT = 20.0

# Manual mapping from target labels to columns in the Ruggeri dataframe.
# Leave values as None to use automatic alias matching.
RUGGERI_MANUAL_MAP = {
    "P1_Allais_certainty": None,
    "P3_Strong_certainty": None,
    "P7_Reflection": None,
    "P11_Isolation": None,
    "P16_Small_prob_gain": None,
    "P17_Small_prob_loss": None,
}

# If a choice item is encoded 1=A and 2=B, the notebook assumes A is the risky/gamble option.
# Override any column here if needed, e.g. {"Q1": ["A", 1]} or {"P3": [2]}.
RISKY_VALUE_OVERRIDES = {}

RNG_SEED = 20260610
rng = np.random.default_rng(RNG_SEED)


# ## Frozen predictions from the submitted manuscript
# 
# These are the paper's reported frozen predictions, expressed as proportions. They are not re-fit in this notebook.
# 
# For a stronger revision, the final manuscript should state that these numbers were treated as frozen before looking at the public-data validation results.

# In[ ]:


FROZEN_PAPER_PREDICTIONS = {
    # Game targets from manuscript Table II
    "UG_mean_offer": 0.480,
    "UG_modal_offer": 0.480,
    "Dictator_mean_giving": 0.320,
    "Responder_MAO": 0.340,
    "PG_round_1": 0.500,
    "PG_round_3": 0.480,
    "PG_round_5": 0.460,
    "PG_round_8": 0.430,
    "PG_round_10": 0.400,
    # Prospect-theory targets from manuscript Table II: proportion choosing risky option
    "P1_Allais_certainty": 0.266,
    "P3_Strong_certainty": 0.154,
    "P7_Reflection": 0.842,
    "P11_Isolation": 0.154,
    "P16_Small_prob_gain": 0.507,
    "P17_Small_prob_loss": 0.506,
    # Historical target
    "Guth_1982_ultimatum_offer": 0.350,
}

pd.Series(FROZEN_PAPER_PREDICTIONS, name="prediction").to_frame()


# ## Download helpers

# In[ ]:


USER_AGENT = "tcss-public-data-analysis/0.1 (academic reproducibility notebook)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})


def safe_filename(name: str, default: str = "downloaded_file") -> str:
    name = unquote(str(name)).strip().replace("\\", "/").split("/")[-1]
    name = re.sub(r"[^A-Za-z0-9._ -]+", "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name or default


def request_json(url: str, *, timeout: int = 60) -> dict[str, Any]:
    r = SESSION.get(url, timeout=timeout, headers={"Accept": "application/json"})
    r.raise_for_status()
    return r.json()


def stream_download(url: str, out_path: Path, *, overwrite: bool = False, min_bytes: int = 1, timeout: int = 120) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size >= min_bytes and not overwrite:
        return out_path

    with SESSION.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype and out_path.suffix.lower() not in {".html", ".htm"}:
            preview = r.text[:500] if hasattr(r, "text") else ""
            raise RuntimeError(f"Download URL returned HTML rather than data: {url}\n{preview[:300]}")
        tmp = out_path.with_suffix(out_path.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        tmp.replace(out_path)

    if out_path.stat().st_size < min_bytes:
        raise RuntimeError(f"Downloaded file is too small: {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def filename_from_headers(headers: dict[str, str], default_name: str) -> str:
    cd = headers.get("content-disposition", "") or headers.get("Content-Disposition", "")
    # Handles both filename="x.csv" and filename*=UTF-8''x.csv forms well enough for OSF/ICPSR.
    m = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", cd, flags=re.IGNORECASE)
    if m:
        return safe_filename(m.group(1), default=default_name)
    ctype = headers.get("content-type", "").lower()
    ext = ""
    if "zip" in ctype:
        ext = ".zip"
    elif "csv" in ctype or "text/plain" in ctype:
        ext = ".csv"
    elif "stata" in ctype or "octet-stream" in ctype:
        ext = Path(default_name).suffix or ".bin"
    if Path(default_name).suffix or not ext:
        return safe_filename(default_name)
    return safe_filename(default_name + ext)


def stream_download_auto_filename(url: str, dest_dir: Path, *, default_name: str, overwrite: bool = False, min_bytes: int = 1, timeout: int = 120) -> Path:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with SESSION.get(url, stream=True, timeout=timeout, allow_redirects=True) as r:
        r.raise_for_status()
        out_path = dest_dir / filename_from_headers(r.headers, default_name)
        if out_path.exists() and out_path.stat().st_size >= min_bytes and not overwrite:
            return out_path
        ctype = r.headers.get("content-type", "").lower()
        if "text/html" in ctype and out_path.suffix.lower() not in {".html", ".htm"}:
            preview = r.text[:500] if hasattr(r, "text") else ""
            raise RuntimeError(f"Download URL returned HTML rather than data: {url}\n{preview[:300]}")
        tmp = out_path.with_suffix(out_path.suffix + ".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        tmp.replace(out_path)
    if out_path.stat().st_size < min_bytes:
        raise RuntimeError(f"Downloaded file is too small: {out_path} ({out_path.stat().st_size} bytes)")
    return out_path


def paginated_jsonapi_items(url: str, *, timeout: int = 60, max_pages: int = 200) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 0
    while url:
        page += 1
        if page > max_pages:
            raise RuntimeError(f"Too many paginated pages while reading {url}")
        data = request_json(url, timeout=timeout)
        page_items = data.get("data", [])
        if isinstance(page_items, dict):
            page_items = [page_items]
        items.extend(page_items)
        url = (data.get("links") or {}).get("next")
    return items


def maybe_extract_archives(root: Path) -> list[Path]:
    extracted = []
    for p in list(root.rglob("*.zip")):
        dest = p.with_suffix("")
        marker = dest / ".extracted_from_zip"
        if marker.exists():
            continue
        dest.mkdir(parents=True, exist_ok=True)
        try:
            shutil.unpack_archive(str(p), str(dest))
            marker.write_text(str(p), encoding="utf-8")
            extracted.append(dest)
        except Exception as e:
            warnings.warn(f"Could not extract {p}: {e}")
    return extracted


# ## Download Fraser and Nettle from Zenodo

# In[ ]:


def zenodo_file_entries(record: dict[str, Any]) -> list[dict[str, Any]]:
    files = record.get("files", [])
    if isinstance(files, dict) and "entries" in files:
        entries = []
        for key, value in files["entries"].items():
            item = dict(value)
            item.setdefault("key", key)
            entries.append(item)
        return entries
    if isinstance(files, list):
        return files
    return []


def download_zenodo_record(record_id: str, dest_dir: Path, *, overwrite: bool = False) -> list[Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    api_url = f"https://zenodo.org/api/records/{record_id}"
    downloaded: list[Path] = []

    try:
        record = request_json(api_url)
        entries = zenodo_file_entries(record)
        if not entries:
            raise RuntimeError("Zenodo API returned no file entries")
        for entry in entries:
            key = entry.get("key") or entry.get("filename") or entry.get("name")
            links = entry.get("links", {}) or {}
            url = links.get("self") or links.get("download") or links.get("content")
            if not key or not url:
                continue
            out = dest_dir / safe_filename(key)
            print(f"Zenodo: downloading {key}")
            downloaded.append(stream_download(url, out, overwrite=overwrite))
        return downloaded
    except Exception as e:
        warnings.warn(f"Zenodo API download failed, trying static file URLs. Reason: {e}")

    # Static fallback for this record.
    known_files = ["data analysis script.r", "Experiment_1.csv", "Experiment_2.csv", "Experiment_2_time.csv"]
    for fname in known_files:
        url = f"https://zenodo.org/records/{record_id}/files/{quote(fname)}?download=1"
        out = dest_dir / safe_filename(fname)
        print(f"Zenodo fallback: downloading {fname}")
        downloaded.append(stream_download(url, out, overwrite=overwrite))
    return downloaded

fraser_dir = RAW_DIR / "fraser_nettle_zenodo_3764693"
try:
    fraser_files = download_zenodo_record(ZENODO_FRASER_NETTLE_RECORD_ID, fraser_dir)
    print("Downloaded Fraser/Nettle files:")
    for p in fraser_files:
        print(" -", p.name, p.stat().st_size, "bytes")
except Exception as e:
    print("Fraser/Nettle download failed:")
    print(e)


# ## Download Ruggeri et al. from OSF
# 
# This function recursively walks public OSF components and OSF storage folders. It downloads data-like files, not every manuscript or image. If OSF changes the project layout, inspect the printed inventory and update `RUGGERI_OSF_IDS` or `RUGGERI_MANUAL_MAP` above.

# In[ ]:


DATA_EXTENSIONS = {
    ".csv", ".tsv", ".txt", ".xlsx", ".xls", ".sav", ".dta", ".feather", ".rds", ".rdata", ".parquet", ".zip"
}


def osf_list_node_storage_files(node_id: str, *, storage_url: str | None = None, prefix: str = "") -> list[dict[str, Any]]:
    if storage_url is None:
        storage_url = f"https://api.osf.io/v2/nodes/{node_id}/files/osfstorage/"
    files: list[dict[str, Any]] = []
    try:
        items = paginated_jsonapi_items(storage_url)
    except Exception as e:
        warnings.warn(f"Could not list OSF storage for node {node_id}: {e}")
        return files

    for item in items:
        attrs = item.get("attributes", {}) or {}
        links = item.get("links", {}) or {}
        name = safe_filename(attrs.get("name") or attrs.get("materialized_path") or item.get("id", "osf_file"))
        kind = attrs.get("kind")
        materialized = attrs.get("materialized_path") or f"/{prefix}{name}"
        if kind == "folder":
            rel = item.get("relationships", {}) or {}
            child_url = (((rel.get("files") or {}).get("links") or {}).get("related") or {}).get("href")
            if child_url:
                files.extend(osf_list_node_storage_files(node_id, storage_url=child_url, prefix=f"{prefix}{name}/"))
            continue
        download_url = links.get("download")
        if download_url:
            files.append({
                "node_id": node_id,
                "name": name,
                "materialized_path": materialized,
                "download_url": download_url,
                "size": attrs.get("size"),
            })
    return files


def osf_child_nodes(node_id: str) -> list[str]:
    url = f"https://api.osf.io/v2/nodes/{node_id}/children/"
    try:
        items = paginated_jsonapi_items(url)
        return [str(item.get("id")) for item in items if item.get("id")]
    except Exception:
        return []


def walk_osf_project(node_id: str, *, visited: set[str] | None = None) -> list[dict[str, Any]]:
    if visited is None:
        visited = set()
    if node_id in visited:
        return []
    visited.add(node_id)

    all_files = osf_list_node_storage_files(node_id)
    for child in osf_child_nodes(node_id):
        all_files.extend(walk_osf_project(child, visited=visited))
    return all_files


def download_osf_data(osf_ids: list[str], dest_dir: Path, *, overwrite: bool = False) -> list[Path]:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    seen_urls: set[str] = set()

    for osf_id in osf_ids:
        print(f"Trying OSF ID: {osf_id}")
        files = walk_osf_project(osf_id)
        data_files = []
        for f in files:
            suffix = Path(f["name"]).suffix.lower()
            if suffix in DATA_EXTENSIONS:
                data_files.append(f)
        if data_files:
            print(f"Found {len(data_files)} data-like files under OSF ID {osf_id}")
            for f in data_files:
                url = f["download_url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                rel_name = safe_filename(f.get("materialized_path") or f["name"])
                out = dest_dir / f"{osf_id}_{rel_name}"
                try:
                    print("OSF: downloading", f.get("materialized_path") or f["name"])
                    downloaded.append(stream_download(url, out, overwrite=overwrite))
                except Exception as e:
                    warnings.warn(f"Could not download OSF file {f.get('name')}: {e}")
            continue

        # If the short ID is a direct OSF file link rather than a node, try /download.
        direct_url = f"https://osf.io/{osf_id}/download"
        try:
            print(f"No node files found for {osf_id}; trying direct OSF download link.")
            downloaded.append(stream_download_auto_filename(direct_url, dest_dir, default_name=f"osf_{osf_id}_download", overwrite=overwrite, min_bytes=100))
        except Exception as e:
            warnings.warn(f"Direct OSF download failed for {osf_id}: {e}")

    maybe_extract_archives(dest_dir)
    return downloaded

ruggeri_dir = RAW_DIR / "ruggeri_osf"
try:
    ruggeri_files = download_osf_data(RUGGERI_OSF_IDS, ruggeri_dir)
    print("Downloaded Ruggeri/OSF files:")
    for p in ruggeri_files:
        print(" -", p.name, p.stat().st_size, "bytes")
except Exception as e:
    print("Ruggeri/OSF download failed:")
    print(e)


# ## Optional: try openICPSR direct download
# 
# openICPSR public projects can still require a browser session, terms acceptance, or login. This cell tries the direct terms/download URL. If it fails, manually download `20100982_DATA.dta` from openICPSR project 112485 and put it at:
# 
# `tcss_public_data_analysis/data_raw/openicpsr_112485/20100982_DATA.dta`

# In[ ]:


def download_openicpsr_stakes(dest_dir: Path, *, overwrite: bool = False) -> Path | None:
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / OPENICPSR_DTA_FILENAME
    if out.exists() and out.stat().st_size > 1000 and not overwrite:
        print("Using existing openICPSR file:", out)
        return out

    encoded_path = quote(f"/openicpsr/{OPENICPSR_PROJECT_ID}/fcr:versions/V1/data/{OPENICPSR_DTA_FILENAME}", safe="")
    url = (
        f"https://www.openicpsr.org/openicpsr/project/{OPENICPSR_PROJECT_ID}/version/V1/download/terms"
        f"?path={encoded_path}&type=file"
    )
    try:
        print("Trying openICPSR direct download...")
        p = stream_download(url, out, overwrite=overwrite, min_bytes=1000)
        print("Downloaded openICPSR file:", p)
        return p
    except Exception as e:
        print("Automatic openICPSR download did not complete. This is common when terms/login are required.")
        print("Reason:", e)
        print("Manual fallback: download 20100982_DATA.dta from openICPSR project 112485 and place it here:")
        print(out)
        return None

openicpsr_dir = RAW_DIR / "openicpsr_112485"
openicpsr_dta = download_openicpsr_stakes(openicpsr_dir)


# ## Table loaders and data inventory

# In[ ]:


def load_table(path: Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".tsv", ".txt"}:
        # Try tab first; fall back to comma.
        try:
            return pd.read_csv(path, sep="\t")
        except Exception:
            return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    if suffix == ".dta":
        return pd.read_stata(path, convert_categoricals=False)
    if suffix == ".sav":
        import pyreadstat
        df, meta = pyreadstat.read_sav(str(path))
        return df
    if suffix == ".feather":
        return pd.read_feather(path)
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in {".rds", ".rdata"}:
        import pyreadr
        result = pyreadr.read_r(str(path))
        if not result:
            raise ValueError(f"No data frames found in {path}")
        # Return the largest object.
        return max(result.values(), key=lambda x: getattr(x, "shape", (0, 0))[0])
    raise ValueError(f"Unsupported table extension: {path}")


def discover_table_files(root: Path) -> list[Path]:
    suffixes = {".csv", ".tsv", ".txt", ".xlsx", ".xls", ".dta", ".sav", ".feather", ".parquet", ".rds", ".rdata"}
    return sorted([p for p in Path(root).rglob("*") if p.is_file() and p.suffix.lower() in suffixes])


def inventory_tables(root: Path, *, max_preview_rows: int = 3) -> pd.DataFrame:
    rows = []
    for path in discover_table_files(root):
        try:
            df = load_table(path)
            rows.append({
                "path": str(path),
                "file": path.name,
                "rows": len(df),
                "cols": df.shape[1],
                "columns_preview": ", ".join(map(str, list(df.columns[:12]))),
            })
        except Exception as e:
            rows.append({"path": str(path), "file": path.name, "rows": np.nan, "cols": np.nan, "columns_preview": f"LOAD FAILED: {e}"})
    inv = pd.DataFrame(rows).sort_values(["rows", "cols"], ascending=False, na_position="last") if rows else pd.DataFrame()
    if not inv.empty:
        inv.to_csv(OUT_DIR / "table_inventory.csv", index=False)
    return inv

inventory = inventory_tables(RAW_DIR)
inventory


# ## Statistical helpers

# In[ ]:


def wilson_ci(k: float, n: float, alpha: float = 0.05) -> tuple[float, float]:
    if n <= 0:
        return (np.nan, np.nan)
    z = norm.ppf(1 - alpha / 2)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return max(0.0, center - half), min(1.0, center + half)


def bootstrap_mean_ci(values: Iterable[float], n_boot: int = 2000, alpha: float = 0.05, seed: int = RNG_SEED) -> tuple[float, float, float, int]:
    x = pd.Series(values).dropna().astype(float).to_numpy()
    n = len(x)
    if n == 0:
        return np.nan, np.nan, np.nan, 0
    rng_local = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        means[i] = rng_local.choice(x, size=n, replace=True).mean()
    lo, hi = np.quantile(means, [alpha / 2, 1 - alpha / 2])
    return float(x.mean()), float(lo), float(hi), int(n)


def mae(obs: Iterable[float], pred: Iterable[float]) -> float:
    o = np.asarray(list(obs), dtype=float)
    p = np.asarray(list(pred), dtype=float)
    mask = np.isfinite(o) & np.isfinite(p)
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs(o[mask] - p[mask])))


def weighted_mae(obs: Iterable[float], pred: Iterable[float], weights: Iterable[float]) -> float:
    o = np.asarray(list(obs), dtype=float)
    p = np.asarray(list(pred), dtype=float)
    w = np.asarray(list(weights), dtype=float)
    mask = np.isfinite(o) & np.isfinite(p) & np.isfinite(w) & (w > 0)
    if mask.sum() == 0:
        return np.nan
    return float(np.average(np.abs(o[mask] - p[mask]), weights=w[mask]))


def coverage_rate(df: pd.DataFrame, pred_col: str = "pred", lo_col: str = "ci_low", hi_col: str = "ci_high") -> float:
    ok = df[pred_col].between(df[lo_col], df[hi_col])
    return float(ok.mean()) if len(ok) else np.nan


def posterior_predictive_binomial_p(observed_rate: float, n: int, pred: float, n_sim: int = 20000, seed: int = RNG_SEED) -> float:
    """Two-sided posterior-predictive/binomial tail check around a fixed model probability."""
    if not np.isfinite(observed_rate) or not np.isfinite(pred) or n <= 0:
        return np.nan
    p = float(np.clip(pred, 1e-9, 1 - 1e-9))
    k_obs = int(round(observed_rate * n))
    expected = n * p
    obs_dev = abs(k_obs - expected)
    rng_local = np.random.default_rng(seed)
    sims = rng_local.binomial(n, p, size=n_sim)
    sim_dev = np.abs(sims - expected)
    return float(np.mean(sim_dev >= obs_dev))


def normalized_name(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(s).lower())


# # Ruggeri et al. prospect-theory replication analysis
# 
# The key manuscript upgrade is to evaluate the prospect-theory side on a large public replication rather than only the six classic aggregate targets. The code below:
# 
# 1. Finds the likely Ruggeri participant-level table.
# 2. Lists binary choice columns and their choice rates.
# 3. Maps the six manuscript prospect-theory targets if possible.
# 4. Computes item-level rates, Wilson intervals, bootstrap intervals, MAE, weighted MAE, and country-level heterogeneity.

# In[ ]:


RUGGERI_TARGETS = {
    "P1_Allais_certainty": {
        "aliases": ["1", "P1", "Q1", "Problem1", "Problem_1", "KT1", "Item1", "Choice1", "X1"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P1_Allais_certainty"],
        "description": "Allais/certainty effect; risky option vs certain 2400-like option",
    },
    "P3_Strong_certainty": {
        "aliases": ["3", "P3", "Q3", "Problem3", "Problem_3", "KT3", "Item3", "Choice3", "X3"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P3_Strong_certainty"],
        "description": "80% chance of large gain vs certain smaller gain",
    },
    "P7_Reflection": {
        "aliases": ["7", "P7", "Q7", "Problem7", "Problem_7", "KT7", "Item7", "Choice7", "X7"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P7_Reflection"],
        "description": "loss-domain reflection of P3",
    },
    "P11_Isolation": {
        "aliases": ["11", "P11", "Q11", "Problem11", "Problem_11", "KT11", "Item11", "Choice11", "X11"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P11_Isolation"],
        "description": "isolation/two-stage framing item",
    },
    "P16_Small_prob_gain": {
        "aliases": ["16", "P16", "Q16", "Problem16", "Problem_16", "KT16", "Item16", "Choice16", "X16"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P16_Small_prob_gain"],
        "description": "small-probability gain item",
    },
    "P17_Small_prob_loss": {
        "aliases": ["17", "P17", "Q17", "Problem17", "Problem_17", "KT17", "Item17", "Choice17", "X17"],
        "prediction": FROZEN_PAPER_PREDICTIONS["P17_Small_prob_loss"],
        "description": "small-probability loss/insurance-like item",
    },
}


def binary_candidate_columns(df: pd.DataFrame, *, min_nonmissing: int = 50, max_unique: int = 6) -> list[str]:
    cols = []
    for col in df.columns:
        s = df[col].dropna()
        if len(s) < min_nonmissing:
            continue
        # Exclude obvious IDs, timestamps, and free-text columns.
        ncol = normalized_name(col)
        if any(tok in ncol for tok in ["id", "time", "date", "duration", "age", "country", "language", "gender"]):
            continue
        uniques = pd.Series(s.unique())
        if len(uniques) <= max_unique:
            cols.append(col)
    return cols


def find_likely_ruggeri_table(root: Path) -> tuple[Path | None, pd.DataFrame | None]:
    candidates = []
    for path in discover_table_files(root):
        try:
            df = load_table(path)
        except Exception:
            continue
        bin_cols = binary_candidate_columns(df, min_nonmissing=max(20, min(200, len(df) // 10)))
        score = len(df) * max(1, len(bin_cols))
        name_score = 100000 if any(tok in path.name.lower() for tok in ["prospect", "ruggeri", "ptr", "data"]) else 0
        candidates.append((score + name_score, path, df, len(bin_cols)))
    if not candidates:
        return None, None
    candidates.sort(key=lambda x: x[0], reverse=True)
    print("Top likely Ruggeri tables:")
    for score, path, df, nbin in candidates[:10]:
        print(f" - {path.name}: rows={len(df)}, cols={df.shape[1]}, binary_candidates={nbin}, score={score:.0f}")
    return candidates[0][1], candidates[0][2]

ruggeri_path, ruggeri_df = find_likely_ruggeri_table(ruggeri_dir)
if ruggeri_df is None:
    print("No Ruggeri table was loaded. Check the OSF download and the table inventory.")
else:
    print("Selected Ruggeri table:", ruggeri_path)
    display(ruggeri_df.head())
    print("Shape:", ruggeri_df.shape)


# In[ ]:


def choice_to_binary(s: pd.Series, *, risky_values: Iterable[Any] | None = None) -> pd.Series:
    # Convert a binary survey column to 1=risky/gamble/A and 0=other.
    # This is intentionally conservative. Verify item coding before final manuscript claims.
    x = s.copy()
    if risky_values is not None:
        rv = set(str(v).strip().lower() for v in risky_values)
        return x.map(lambda v: np.nan if pd.isna(v) else (1.0 if str(v).strip().lower() in rv else 0.0))

    nonmiss = x.dropna()
    if nonmiss.empty:
        return pd.Series(np.nan, index=s.index)

    # Numeric encodings.
    x_num = pd.to_numeric(nonmiss, errors="coerce")
    if x_num.notna().mean() > 0.95:
        vals = sorted(pd.unique(x_num.dropna()))
        if set(vals).issubset({0, 1}):
            return pd.to_numeric(x, errors="coerce").map(lambda v: np.nan if pd.isna(v) else float(v == 1))
        if set(vals).issubset({1, 2}):
            # Common Qualtrics/SPSS coding: 1 = first option/A, 2 = second option/B.
            return pd.to_numeric(x, errors="coerce").map(lambda v: np.nan if pd.isna(v) else float(v == 1))
        if len(vals) == 2:
            # Fallback: smaller code is first option/A.
            return pd.to_numeric(x, errors="coerce").map(lambda v: np.nan if pd.isna(v) else float(v == vals[0]))

    # String encodings.
    positive_tokens = {
        "a", "option a", "option_a", "prospect a", "prospect_a", "lottery a", "lottery_a",
        "gamble", "risky", "risk", "yes", "true", "1", "r"
    }
    x_str = x.astype("string").str.strip().str.lower()
    uniques = sorted([u for u in x_str.dropna().unique()])
    if len(uniques) == 2:
        return x_str.map(lambda v: np.nan if pd.isna(v) else float(v in positive_tokens or v == uniques[0]))
    return pd.Series(np.nan, index=s.index)


def summarize_binary_column(df: pd.DataFrame, col: str, *, risky_values: Iterable[Any] | None = None) -> dict[str, Any]:
    y = choice_to_binary(df[col], risky_values=risky_values).dropna()
    n = len(y)
    k = int(y.sum()) if n else 0
    lo, hi = wilson_ci(k, n) if n else (np.nan, np.nan)
    return {"column": col, "n": n, "risky_rate": k / n if n else np.nan, "ci_low": lo, "ci_high": hi, "successes": k}

if ruggeri_df is not None:
    ruggeri_binary_cols = binary_candidate_columns(ruggeri_df, min_nonmissing=max(50, len(ruggeri_df)//20))
    binary_summary = pd.DataFrame([summarize_binary_column(ruggeri_df, col) for col in ruggeri_binary_cols])
    binary_summary = binary_summary.sort_values("column")
    binary_summary.to_csv(OUT_DIR / "ruggeri_binary_column_summary.csv", index=False)
    display(binary_summary.head(50))
    print(f"Candidate binary columns saved to: {OUT_DIR / 'ruggeri_binary_column_summary.csv'}")
else:
    binary_summary = pd.DataFrame()


# In[ ]:


def resolve_ruggeri_mapping(df: pd.DataFrame) -> dict[str, str | None]:
    col_by_norm = {normalized_name(c): c for c in df.columns}
    resolved = {}
    for target, spec in RUGGERI_TARGETS.items():
        manual = RUGGERI_MANUAL_MAP.get(target)
        if manual:
            resolved[target] = manual if manual in df.columns else None
            continue
        found = None
        for alias in spec["aliases"]:
            n_alias = normalized_name(alias)
            if n_alias in col_by_norm:
                found = col_by_norm[n_alias]
                break
        resolved[target] = found
    return resolved


def evaluate_ruggeri_frozen_predictions(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    rows = []
    for target, col in mapping.items():
        if not col:
            rows.append({
                "target": target,
                "column": None,
                "description": RUGGERI_TARGETS[target]["description"],
                "n": 0,
                "observed": np.nan,
                "ci_low": np.nan,
                "ci_high": np.nan,
                "pred": RUGGERI_TARGETS[target]["prediction"],
                "error": np.nan,
                "abs_error": np.nan,
                "covered_by_95ci": False,
                "note": "No column mapped. Set RUGGERI_MANUAL_MAP after inspecting binary column summary.",
            })
            continue
        risky_values = RISKY_VALUE_OVERRIDES.get(col)
        y = choice_to_binary(df[col], risky_values=risky_values).dropna()
        n = len(y)
        k = int(y.sum()) if n else 0
        obs = k / n if n else np.nan
        lo, hi = wilson_ci(k, n) if n else (np.nan, np.nan)
        pred = RUGGERI_TARGETS[target]["prediction"]
        rows.append({
            "target": target,
            "column": col,
            "description": RUGGERI_TARGETS[target]["description"],
            "n": n,
            "observed": obs,
            "ci_low": lo,
            "ci_high": hi,
            "pred": pred,
            "error": pred - obs if np.isfinite(obs) else np.nan,
            "abs_error": abs(pred - obs) if np.isfinite(obs) else np.nan,
            "covered_by_95ci": bool(lo <= pred <= hi) if n else False,
            "postpred_p": posterior_predictive_binomial_p(obs, n, pred) if n else np.nan,
            "note": "",
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "ruggeri_frozen_prediction_evaluation.csv", index=False)
    return out

if ruggeri_df is not None:
    ruggeri_mapping = resolve_ruggeri_mapping(ruggeri_df)
    print("Resolved Ruggeri mapping:")
    print(json.dumps(ruggeri_mapping, indent=2))
    ruggeri_eval = evaluate_ruggeri_frozen_predictions(ruggeri_df, ruggeri_mapping)
    display(ruggeri_eval)
    mapped = ruggeri_eval.dropna(subset=["observed", "pred"])
    print("Mapped targets:", len(mapped), "/", len(ruggeri_eval))
    if len(mapped):
        print("Unweighted MAE:", mae(mapped["observed"], mapped["pred"]))
        print("N-weighted MAE:", weighted_mae(mapped["observed"], mapped["pred"], mapped["n"]))
        print("95% CI coverage:", coverage_rate(mapped))
else:
    ruggeri_eval = pd.DataFrame()


# In[ ]:


def plot_prediction_evaluation(df: pd.DataFrame, title: str, filename: str) -> None:
    d = df.dropna(subset=["observed", "pred"]).copy()
    if d.empty:
        print("No mapped rows to plot.")
        return
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(d))
    ax.errorbar(x, d["observed"], yerr=[d["observed"] - d["ci_low"], d["ci_high"] - d["observed"]], fmt="o", capsize=3, label="Observed 95% CI")
    ax.scatter(x, d["pred"], marker="x", label="Frozen geometric prediction")
    ax.set_xticks(x)
    ax.set_xticklabels(d["target"], rotation=45, ha="right")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proportion choosing risky/A option")
    ax.set_title(title)
    ax.legend()
    fig.tight_layout()
    path = FIG_DIR / filename
    fig.savefig(path, dpi=200)
    print("Saved figure:", path)

plot_prediction_evaluation(ruggeri_eval, "Ruggeri public-data evaluation of frozen PT predictions", "ruggeri_frozen_predictions.png")


# In[ ]:


def find_country_column(df: pd.DataFrame) -> str | None:
    candidates = []
    for col in df.columns:
        n = normalized_name(col)
        if any(tok in n for tok in ["country", "nation", "location", "site"]):
            nunique = df[col].nunique(dropna=True)
            if 2 <= nunique <= 100:
                candidates.append((nunique, col))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None


def ruggeri_country_level(df: pd.DataFrame, mapping: dict[str, str | None]) -> pd.DataFrame:
    country_col = find_country_column(df)
    if not country_col:
        print("No country/site column detected.")
        return pd.DataFrame()
    rows = []
    for target, col in mapping.items():
        if not col:
            continue
        risky_values = RISKY_VALUE_OVERRIDES.get(col)
        y = choice_to_binary(df[col], risky_values=risky_values)
        temp = pd.DataFrame({"country": df[country_col], "choice": y}).dropna()
        for country, g in temp.groupby("country"):
            n = len(g)
            k = int(g["choice"].sum())
            lo, hi = wilson_ci(k, n)
            rows.append({
                "target": target,
                "column": col,
                "country": country,
                "n": n,
                "observed": k / n,
                "ci_low": lo,
                "ci_high": hi,
                "pred": RUGGERI_TARGETS[target]["prediction"],
                "error": RUGGERI_TARGETS[target]["prediction"] - k / n,
                "abs_error": abs(RUGGERI_TARGETS[target]["prediction"] - k / n),
                "postpred_p": posterior_predictive_binomial_p(k / n, n, RUGGERI_TARGETS[target]["prediction"]),
            })
    out = pd.DataFrame(rows)
    if not out.empty:
        out.to_csv(OUT_DIR / "ruggeri_country_level_evaluation.csv", index=False)
    return out

if ruggeri_df is not None and 'ruggeri_mapping' in globals():
    ruggeri_country_eval = ruggeri_country_level(ruggeri_df, ruggeri_mapping)
    display(ruggeri_country_eval.head(30))
    if not ruggeri_country_eval.empty:
        print("Country-level N-weighted MAE:", weighted_mae(ruggeri_country_eval["observed"], ruggeri_country_eval["pred"], ruggeri_country_eval["n"]))
        print("Country-level rows:", len(ruggeri_country_eval))
else:
    ruggeri_country_eval = pd.DataFrame()


# In[ ]:


# Plot country heterogeneity for the first successfully mapped Ruggeri target.
if not ruggeri_country_eval.empty:
    first_target = ruggeri_country_eval["target"].iloc[0]
    d = ruggeri_country_eval.query("target == @first_target").sort_values("observed")
    fig, ax = plt.subplots(figsize=(8, max(4, 0.25 * len(d))))
    y = np.arange(len(d))
    ax.errorbar(d["observed"], y, xerr=[d["observed"] - d["ci_low"], d["ci_high"] - d["observed"]], fmt="o", capsize=2)
    ax.axvline(d["pred"].iloc[0], linestyle="--", label="Frozen prediction")
    ax.set_yticks(y)
    ax.set_yticklabels(d["country"])
    ax.set_xlim(0, 1)
    ax.set_xlabel("Observed risky/A choice rate")
    ax.set_title(f"Ruggeri country heterogeneity: {first_target}")
    ax.legend()
    fig.tight_layout()
    path = FIG_DIR / f"ruggeri_country_{first_target}.png"
    fig.savefig(path, dpi=200)
    print("Saved figure:", path)
else:
    print("No country-level plot available.")


# # Fraser and Nettle game-side analysis
# 
# This section uses the public Zenodo data to recompute the bargaining/public-goods targets and uncertainty intervals from participant-level data.

# In[ ]:


def load_named_file(root: Path, pattern: str) -> tuple[Path | None, pd.DataFrame | None]:
    matches = [p for p in discover_table_files(root) if re.search(pattern, p.name, flags=re.IGNORECASE)]
    if not matches:
        return None, None
    # Prefer CSV if present.
    matches.sort(key=lambda p: (p.suffix.lower() != ".csv", len(p.name)))
    path = matches[0]
    return path, load_table(path)

exp1_path, exp1_df = load_named_file(fraser_dir, r"Experiment[_ -]?1")
exp2_path, exp2_df = load_named_file(fraser_dir, r"Experiment[_ -]?2(?![_ -]?time)")
time_path, time_df = load_named_file(fraser_dir, r"Experiment[_ -]?2[_ -]?time")

print("Experiment 1:", exp1_path, None if exp1_df is None else exp1_df.shape)
print("Experiment 2:", exp2_path, None if exp2_df is None else exp2_df.shape)
print("Experiment 2 time:", time_path, None if time_df is None else time_df.shape)
if exp1_df is not None:
    display(exp1_df.head())
if exp2_df is not None:
    display(exp2_df.head())


# In[ ]:


def numeric_columns(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in df.columns:
        x = pd.to_numeric(df[col], errors="coerce")
        if x.notna().sum() >= max(10, len(df) * 0.1):
            cols.append(col)
    return cols


def as_percentage(series: pd.Series, *, endowment: float | None = None) -> pd.Series:
    x = pd.to_numeric(series, errors="coerce")
    if x.dropna().empty:
        return x
    mx = x.quantile(0.99)
    if mx <= 1.5:
        return x * 100.0
    if endowment is not None and mx <= endowment * 1.05:
        return x / endowment * 100.0
    if mx <= 100.0:
        return x
    return x


def column_name_matches(col: str, patterns: list[str]) -> bool:
    n = normalized_name(col)
    return any(re.search(p, n) for p in patterns)


def summarize_candidate_game_columns(df: pd.DataFrame, *, endowment: float) -> pd.DataFrame:
    rows = []
    for col in numeric_columns(df):
        ncol = normalized_name(col)
        if any(tok in ncol for tok in ["offer", "propos", "give", "giving", "mao", "min", "accept", "contrib", "contribution", "punish"]):
            pct = as_percentage(df[col], endowment=endowment)
            mean_, lo, hi, n = bootstrap_mean_ci(pct)
            rows.append({"column": col, "n": n, "mean_pct": mean_, "ci_low": lo, "ci_high": hi, "raw_min": pd.to_numeric(df[col], errors="coerce").min(), "raw_max": pd.to_numeric(df[col], errors="coerce").max()})
    return pd.DataFrame(rows).sort_values("column") if rows else pd.DataFrame()

if exp1_df is not None:
    exp1_candidates = summarize_candidate_game_columns(exp1_df, endowment=ULTIMATUM_ENDOWMENT)
    exp1_candidates.to_csv(OUT_DIR / "fraser_experiment1_candidate_game_columns.csv", index=False)
    display(exp1_candidates)
else:
    exp1_candidates = pd.DataFrame()


# In[ ]:


def find_round_column(df: pd.DataFrame) -> str | None:
    candidates = []
    for col in df.columns:
        n = normalized_name(col)
        x = pd.to_numeric(df[col], errors="coerce")
        nunique = x.nunique(dropna=True)
        if ("round" in n or n in {"r", "period"}) and 2 <= nunique <= 50:
            candidates.append((nunique, col))
    if candidates:
        candidates.sort()
        return candidates[0][1]
    return None


def find_contribution_column(df: pd.DataFrame) -> str | None:
    # Per-individual contribution preferred; exclude aggregate/derived columns.
    EXCLUDE_TOKENS = ("group", "pool", "total", "share", "lagged", "punishment", "initial", "final", "payoff", "received", "sent")
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if not any(tok in n for tok in ["contrib", "contribution", "publicgoods", "pgcontrib", "amountcontributed", "tokenscontributed"]):
            continue
        if any(bad in n for bad in EXCLUDE_TOKENS):
            continue
        x = pd.to_numeric(df[col], errors="coerce")
        # Prefer the exact-name "contribution" column when present.
        exact_bonus = 10**9 if n == "contribution" else 0
        candidates.append((x.notna().sum() + exact_bonus, col))
    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None


def wide_contribution_columns(df: pd.DataFrame) -> list[tuple[int, str]]:
    cols = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if not any(tok in n for tok in ["contrib", "contribution", "pg", "publicgoods"]):
            continue
        m = re.search(r"(\d{1,2})$", n)
        if m:
            round_no = int(m.group(1))
            if 1 <= round_no <= 50:
                cols.append((round_no, col))
    return sorted(cols)


def public_goods_round_summary(df: pd.DataFrame, *, endowment: float = PUBLIC_GOODS_ENDOWMENT) -> pd.DataFrame:
    round_col = find_round_column(df)
    contrib_col = find_contribution_column(df)
    rows = []

    if round_col and contrib_col:
        temp = pd.DataFrame({"round": pd.to_numeric(df[round_col], errors="coerce"), "contrib_pct": as_percentage(df[contrib_col], endowment=endowment)}).dropna()
        for r, g in temp.groupby("round"):
            mean_, lo, hi, n = bootstrap_mean_ci(g["contrib_pct"])
            rows.append({"round": int(r), "n": n, "observed": mean_ / 100.0, "ci_low": lo / 100.0, "ci_high": hi / 100.0, "source_format": "long", "round_col": round_col, "contrib_col": contrib_col})
        return pd.DataFrame(rows).sort_values("round")

    wide_cols = wide_contribution_columns(df)
    if wide_cols:
        for r, col in wide_cols:
            pct = as_percentage(df[col], endowment=endowment)
            mean_, lo, hi, n = bootstrap_mean_ci(pct)
            rows.append({"round": r, "n": n, "observed": mean_ / 100.0, "ci_low": lo / 100.0, "ci_high": hi / 100.0, "source_format": "wide", "round_col": None, "contrib_col": col})
        return pd.DataFrame(rows).sort_values("round")

    return pd.DataFrame()

if exp2_df is not None:
    pg_summary = public_goods_round_summary(exp2_df)
    pg_summary.to_csv(OUT_DIR / "fraser_public_goods_round_summary.csv", index=False)
    display(pg_summary.head(25))
else:
    pg_summary = pd.DataFrame()


# In[ ]:


def evaluate_public_goods_predictions(pg_summary: pd.DataFrame) -> pd.DataFrame:
    if pg_summary.empty:
        return pd.DataFrame()
    target_rounds = {
        1: FROZEN_PAPER_PREDICTIONS["PG_round_1"],
        3: FROZEN_PAPER_PREDICTIONS["PG_round_3"],
        5: FROZEN_PAPER_PREDICTIONS["PG_round_5"],
        8: FROZEN_PAPER_PREDICTIONS["PG_round_8"],
        10: FROZEN_PAPER_PREDICTIONS["PG_round_10"],
    }
    rows = []
    for r, pred in target_rounds.items():
        d = pg_summary[pg_summary["round"] == r]
        if d.empty:
            rows.append({"target": f"PG_round_{r}", "round": r, "n": 0, "observed": np.nan, "ci_low": np.nan, "ci_high": np.nan, "pred": pred, "error": np.nan, "abs_error": np.nan, "covered_by_95ci": False})
            continue
        row = d.iloc[0]
        obs = float(row["observed"])
        rows.append({"target": f"PG_round_{r}", "round": r, "n": int(row["n"]), "observed": obs, "ci_low": float(row["ci_low"]), "ci_high": float(row["ci_high"]), "pred": pred, "error": pred - obs, "abs_error": abs(pred - obs), "covered_by_95ci": bool(row["ci_low"] <= pred <= row["ci_high"])})
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "fraser_public_goods_frozen_prediction_evaluation.csv", index=False)
    return out

pg_eval = evaluate_public_goods_predictions(pg_summary)
display(pg_eval)
if not pg_eval.empty:
    mapped = pg_eval.dropna(subset=["observed"])
    print("PG MAE:", mae(mapped["observed"], mapped["pred"]))
    print("PG N-weighted MAE:", weighted_mae(mapped["observed"], mapped["pred"], mapped["n"]))
    print("PG 95% CI coverage:", coverage_rate(mapped))


# In[ ]:


if not pg_summary.empty:
    fig, ax = plt.subplots(figsize=(8, 5))
    d = pg_summary.sort_values("round")
    ax.errorbar(d["round"], d["observed"], yerr=[d["observed"] - d["ci_low"], d["ci_high"] - d["observed"]], fmt="o-", capsize=3, label="Observed")
    if not pg_eval.empty:
        dd = pg_eval.dropna(subset=["observed"])
        ax.scatter(dd["round"], dd["pred"], marker="x", label="Frozen predictions")
    ax.set_xlabel("Round")
    ax.set_ylabel("Mean contribution proportion")
    ax.set_ylim(0, 1)
    ax.set_title("Fraser/Nettle public-goods contribution trajectory")
    ax.legend()
    fig.tight_layout()
    path = FIG_DIR / "fraser_public_goods_trajectory.png"
    fig.savefig(path, dpi=200)
    print("Saved figure:", path)
else:
    print("No public-goods trajectory found. Inspect Experiment_2 columns and update detection logic if needed.")


# ## Ultimatum-game and dictator-game summaries from Fraser/Nettle Experiment 1
# 
# This cell does not assume exact column names. It prints candidate offer/MAO/giving columns with bootstrap confidence intervals. Use the output to select the correct columns for the final manuscript table.

# In[ ]:


def pick_first_matching_column(df: pd.DataFrame, patterns: list[str], *, endowment: float, exclude: tuple[str, ...] = ()) -> str | None:
    candidates = []
    for col in numeric_columns(df):
        n = normalized_name(col)
        if not any(re.search(p, n) for p in patterns):
            continue
        if exclude and any(bad in n for bad in exclude):
            continue
        x = as_percentage(df[col], endowment=endowment)
        candidates.append((x.notna().sum(), col))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]

# Update these manually after inspecting exp1_candidates if the automatic choice is wrong.
EXP1_MANUAL_COLUMNS = {
    "UG_mean_offer": None,
    "Responder_MAO": None,
    "Dictator_mean_giving": None,
}


def evaluate_exp1_game_predictions(df: pd.DataFrame) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame()
    UG_EXCLUDE = ("time", "first", "info")
    auto_cols = {
        "UG_mean_offer": pick_first_matching_column(df, [r"proposedamount", r"\bamount\b", r"offer", r"propos"], endowment=ULTIMATUM_ENDOWMENT, exclude=UG_EXCLUDE),
        "Responder_MAO": pick_first_matching_column(df, [r"lowestaccept", r"minaccept", r"mao", r"minimumoffer", r"acceptthreshold"], endowment=ULTIMATUM_ENDOWMENT, exclude=("highest",)),
        "Dictator_mean_giving": pick_first_matching_column(df, [r"dictator", r"\bdg\b", r"\bgiving\b", r"\bgive\b"], endowment=ULTIMATUM_ENDOWMENT),
    }
    rows = []
    for target, auto_col in auto_cols.items():
        col = EXP1_MANUAL_COLUMNS.get(target) or auto_col
        if not col or col not in df.columns:
            rows.append({"target": target, "column": None, "n": 0, "observed": np.nan, "ci_low": np.nan, "ci_high": np.nan, "pred": FROZEN_PAPER_PREDICTIONS[target], "error": np.nan, "abs_error": np.nan, "covered_by_95ci": False, "note": "No column resolved"})
            continue
        pct = as_percentage(df[col], endowment=ULTIMATUM_ENDOWMENT) / 100.0
        mean_, lo, hi, n = bootstrap_mean_ci(pct)
        pred = FROZEN_PAPER_PREDICTIONS[target]
        rows.append({"target": target, "column": col, "n": n, "observed": mean_, "ci_low": lo, "ci_high": hi, "pred": pred, "error": pred - mean_, "abs_error": abs(pred - mean_), "covered_by_95ci": bool(lo <= pred <= hi), "note": "Verify auto-selected column" if not EXP1_MANUAL_COLUMNS.get(target) else "Manual column"})
    out = pd.DataFrame(rows)
    out.to_csv(OUT_DIR / "fraser_exp1_game_frozen_prediction_evaluation.csv", index=False)
    return out

exp1_eval = evaluate_exp1_game_predictions(exp1_df) if exp1_df is not None else pd.DataFrame()
display(exp1_eval)
if not exp1_eval.empty:
    mapped = exp1_eval.dropna(subset=["observed"])
    print("Experiment 1 mapped targets:", len(mapped), "/", len(exp1_eval))
    print("Experiment 1 MAE:", mae(mapped["observed"], mapped["pred"]))
    print("Experiment 1 N-weighted MAE:", weighted_mae(mapped["observed"], mapped["pred"], mapped["n"]))


# # High-stakes ultimatum boundary-condition test (Andersen et al. 2011)
# 
# The TCSS revision frames the money-zero result as a *context-specific finding* rather than a universal law: monetary stakes are inactive in the studied low-stakes paradigms, but the framework predicts that monetary sensitivity should reactivate in genuinely high-stakes settings.
# 
# Andersen, Ertac, Gneezy, Hoffman & List (2011, AER) is the cleanest empirical test: stakes from Rs 20 to Rs 20,000 (a 1000x range; the highest condition is approximately 1.6x monthly income in their Indonesia sample).
# 
# If money-zero is universal (sigma^2_1 = infinity everywhere), then under the manuscript section VII.A *stake-scaling invariance* argument:
# 
# - mean `percent_offer` should be flat across stakes,
# - rejection rate should be flat across stakes,
# - the logit `reject ~ offer_share + log_stake` should not improve on `reject ~ offer_share`.
# 
# If any of these is violated, money-zero is falsified at high stakes -- exactly the boundary the revised manuscript predicts.
# 
# The cells below load the openICPSR 112485 archive, restrict to Andersen IN==1 by default, compute mean offer/rejection rates per stake level, run the formal invariance tests (chi-square + Kruskal-Wallis + logit likelihood-ratio), and produce the falsification figure.
# 

# In[ ]:


# Load Andersen et al. (2011) "Stakes Matter in Ultimatum Games" data.
# The .dta also contains pooled Slonim-Roth (SR) and Cameron (C) re-analysis
# rows; the published headline analysis uses Andersen's own subset (IN==1).
ANDERSEN_DTA_CANDIDATES = [
    openicpsr_dir / OPENICPSR_DTA_FILENAME,
    openicpsr_dir / "data" / OPENICPSR_DTA_FILENAME,
]
ANDERSEN_DTA = next((p for p in ANDERSEN_DTA_CANDIDATES if p.exists()), None)
ANDERSEN_INCLUDE_POOLED = False  # set True to use all three studies via DaysW

def load_andersen_data() -> pd.DataFrame | None:
    if ANDERSEN_DTA is None or not ANDERSEN_DTA.exists():
        print("Andersen .dta not found in any of:")
        for c in ANDERSEN_DTA_CANDIDATES:
            print(f"  - {c}")
        print("Place the openICPSR 112485 archive there to enable this section.")
        return None
    df = pd.read_stata(ANDERSEN_DTA, convert_categoricals=False)
    print(f"Loaded {df.shape[0]} rows from {ANDERSEN_DTA.name}")
    print(f"Columns: {list(df.columns)}")
    if ANDERSEN_INCLUDE_POOLED:
        sub = df.copy()
        sub["study"] = np.where(sub["IN"]==1, "Andersen",
                                np.where(sub["SR"]==1, "Slonim-Roth", "Cameron"))
    else:
        sub = df[df["IN"]==1].copy()
        sub["study"] = "Andersen"
    sub["reject"] = 1 - sub["accept"]
    sub = sub.dropna(subset=["stakes", "percent_offer", "accept"])
    print(f"Working sample: n={len(sub)} "
          f"({'pooled three studies via DaysW' if ANDERSEN_INCLUDE_POOLED else 'Andersen IN==1 only'})")
    print(f"Stakes levels: {sorted(sub['stakes'].unique())}")
    return sub

andersen_df = load_andersen_data()
if andersen_df is not None:
    display(andersen_df.head())


# In[ ]:


# Descriptive: mean percent_offer and rejection rate per stakes level.
# Under the manuscript's stake-scaling invariance (sigma^2_1 = inf, d_1 inactive),
# both columns should be flat across stakes.

if andersen_df is None or andersen_df.empty:
    andersen_summary = pd.DataFrame()
else:
    rows = []
    for stake, sub in andersen_df.groupby("stakes"):
        n = len(sub)
        po = sub["percent_offer"]
        rj = sub["reject"]
        # CIs on means
        po_se = po.std(ddof=1) / np.sqrt(n)
        rj_se = np.sqrt(rj.mean() * (1 - rj.mean()) / n)
        rows.append({
            "stakes": int(stake),
            "n": n,
            "mean_percent_offer": po.mean(),
            "po_ci_low": po.mean() - 1.96*po_se,
            "po_ci_high": po.mean() + 1.96*po_se,
            "mean_reject": rj.mean(),
            "rj_ci_low": rj.mean() - 1.96*rj_se,
            "rj_ci_high": rj.mean() + 1.96*rj_se,
            # Rejection rate restricted to "unfair" offers (<=20% of pie)
            "reject_unfair_offers": rj[sub["percent_offer"] <= 0.201].mean()
                if (sub["percent_offer"] <= 0.201).any() else np.nan,
            "n_unfair_offers": int((sub["percent_offer"] <= 0.201).sum()),
        })
    andersen_summary = pd.DataFrame(rows).sort_values("stakes")
    andersen_summary.to_csv(OUT_DIR / "andersen_stakes_summary.csv", index=False)
    display(andersen_summary.round(3))

    # Geometric model's stake-scaling-invariance prediction is *flat*. Compute
    # the average prediction (mean of observed percent_offer at stake==20) and
    # report deviations at higher stakes.
    if not andersen_summary.empty:
        baseline_offer = andersen_summary.loc[andersen_summary["stakes"]==20, "mean_percent_offer"].iloc[0]
        baseline_reject = andersen_summary.loc[andersen_summary["stakes"]==20, "mean_reject"].iloc[0]
        andersen_summary["po_dev_from_baseline_pp"] = (andersen_summary["mean_percent_offer"] - baseline_offer) * 100
        andersen_summary["rj_dev_from_baseline_pp"] = (andersen_summary["mean_reject"] - baseline_reject) * 100
        print("\nGeometric stake-scaling-invariance prediction: zero deviation across stakes.")
        print(andersen_summary[["stakes", "mean_percent_offer", "po_dev_from_baseline_pp",
                                  "mean_reject", "rj_dev_from_baseline_pp"]].round(3).to_string(index=False))


# In[ ]:


# Formal tests of stake invariance.
# (a) Chi-square test of equal rejection rates across stakes (Andersen Table 2)
# (b) ANOVA / Kruskal on percent_offer across stakes
# (c) Logit reject ~ percent_offer + log_stake  -- LRT for log_stake coefficient

from scipy.stats import chi2_contingency, kruskal, chi2

def test_stake_invariance(d: pd.DataFrame) -> dict:
    if d is None or d.empty:
        return {}
    # Chi-square on rejection-by-stake contingency
    ct = pd.crosstab(d["stakes"], d["reject"])
    chi2_stat, p_chi2, dof, _ = chi2_contingency(ct)

    # Kruskal-Wallis on percent_offer across stakes
    groups = [g["percent_offer"].values for _, g in d.groupby("stakes")]
    h_stat, p_kw = kruskal(*groups)

    # Logit: reject ~ percent_offer + log(stake)
    dd = d.copy()
    dd["log_stake"] = np.log(dd["stakes"])
    dd["offer_share"] = dd["percent_offer"].clip(1e-6, 1-1e-6)
    m0 = smf.logit("reject ~ offer_share", data=dd).fit(disp=False)
    m1 = smf.logit("reject ~ offer_share + log_stake", data=dd).fit(disp=False)
    lr = 2 * (m1.llf - m0.llf)
    p_lr = float(chi2.sf(lr, df=1))

    return {
        "n": len(d),
        "chi2_reject_by_stake": chi2_stat, "p_chi2": p_chi2,
        "kruskal_offer_by_stake_H": h_stat, "p_kruskal": p_kw,
        "logit_log_stake_coef": float(m1.params.get("log_stake", np.nan)),
        "logit_log_stake_se":   float(m1.bse.get("log_stake", np.nan)),
        "logit_log_stake_OR":   float(np.exp(m1.params.get("log_stake", np.nan))),
        "logit_log_stake_p":    float(m1.pvalues.get("log_stake", np.nan)),
        "LRT_p_stake_vs_offer": p_lr,
        "logit_baseline_aic": float(m0.aic), "logit_with_stake_aic": float(m1.aic),
    }, m0, m1

if andersen_df is not None and not andersen_df.empty:
    invariance_tests, m_offer_only, m_with_stake = test_stake_invariance(andersen_df)
    print("\nStake-invariance test results:")
    for k, v in invariance_tests.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4g}")
        else:
            print(f"  {k}: {v}")
    pd.Series(invariance_tests, name="value").to_csv(OUT_DIR / "andersen_invariance_tests.csv")

    print("\nLogit with log(stakes):")
    print(m_with_stake.summary().tables[1])
else:
    invariance_tests = {}


# In[ ]:


# Money-zero falsification figure.
# Two panels: (1) mean percent_offer by stake, (2) rejection rate by stake,
# both with 95% CIs and the geometric framework's flat-line prediction.

if andersen_df is not None and not andersen_df.empty and not andersen_summary.empty:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    s = andersen_summary.sort_values("stakes")
    x = np.arange(len(s))
    labels = [f"Rs {int(v):,}" for v in s["stakes"]]

    # Panel 1: percent offer
    ax = axes[0]
    yerr = [(s["mean_percent_offer"] - s["po_ci_low"]).values,
            (s["po_ci_high"] - s["mean_percent_offer"]).values]
    ax.bar(x, s["mean_percent_offer"]*100, yerr=np.array(yerr)*100, capsize=4,
           color="#4477AA", label="Observed (mean ± 95% CI)")
    baseline = s["mean_percent_offer"].iloc[0] * 100
    ax.axhline(baseline, ls="--", color="red",
               label=f"Geometric stake-scaling invariance ({baseline:.1f}%)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Mean offer (% of pie)")
    ax.set_title("(a) Proposer behavior by stakes")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(35, baseline*1.5))
    ax.grid(axis="y", alpha=0.3)

    # Panel 2: rejection rate
    ax = axes[1]
    yerr = [(s["mean_reject"] - s["rj_ci_low"]).values,
            (s["rj_ci_high"] - s["mean_reject"]).values]
    ax.bar(x, s["mean_reject"]*100, yerr=np.array(yerr)*100, capsize=4,
           color="#CC6677", label="Observed (mean ± 95% CI)")
    baseline_r = s["mean_reject"].iloc[0] * 100
    ax.axhline(baseline_r, ls="--", color="red",
               label=f"Geometric stake-scaling invariance ({baseline_r:.1f}%)")
    ax.set_xticks(x); ax.set_xticklabels(labels, rotation=20)
    ax.set_ylabel("Rejection rate (%)")
    ax.set_title("(b) Responder behavior by stakes")
    ax.legend(fontsize=9)
    ax.set_ylim(0, max(50, baseline_r*1.5))
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Andersen et al. (2011) high-stakes ultimatum: money-zero boundary",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    path = FIG_DIR / "andersen_money_zero_falsification.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    fig.savefig(FIG_DIR / "andersen_money_zero_falsification.pdf", bbox_inches="tight")
    print(f"Saved: {path}")
else:
    print("No Andersen data — figure skipped.")


# # Combined reviewer-facing summary tables
# 
# The final cell combines available results into one set of CSV files that can be cited in the response letter and used to update manuscript tables/figures.

# In[ ]:


summary_blocks = []
for name, df in [
    ("ruggeri_item", ruggeri_eval if 'ruggeri_eval' in globals() else pd.DataFrame()),
    ("ruggeri_country", ruggeri_country_eval if 'ruggeri_country_eval' in globals() else pd.DataFrame()),
    ("fraser_pg", pg_eval if 'pg_eval' in globals() else pd.DataFrame()),
    ("fraser_exp1", exp1_eval if 'exp1_eval' in globals() else pd.DataFrame()),
]:
    if df is not None and not df.empty and {"observed", "pred", "n"}.issubset(df.columns):
        d = df.dropna(subset=["observed", "pred"]).copy()
        if not d.empty:
            summary_blocks.append({
                "analysis": name,
                "rows": len(d),
                "total_n": int(d["n"].sum()) if "n" in d else np.nan,
                "mae": mae(d["observed"], d["pred"]),
                "weighted_mae": weighted_mae(d["observed"], d["pred"], d["n"]),
                "ci_coverage": coverage_rate(d) if {"ci_low", "ci_high"}.issubset(d.columns) else np.nan,
            })

combined_summary = pd.DataFrame(summary_blocks)
combined_summary.to_csv(OUT_DIR / "combined_public_data_validation_summary.csv", index=False)
display(combined_summary)
print("Outputs written to:", OUT_DIR)
print("Figures written to:", FIG_DIR)


# ## How to use the output in the revision
# 
# Recommended manuscript language if the public-data results are good:
# 
# > We therefore replaced the original six aggregate prospect-theory checks with a public-data validation on Ruggeri et al.'s multinational replication. The geometric predictions were frozen before analysis. We evaluated item-level and country-level risky-choice rates using Wilson and bootstrap confidence intervals, and report both unweighted and sample-size-weighted MAE.
# 
# Recommended language if the results are mixed:
# 
# > The public-data analysis revealed that the original metric captures some aggregate prospect-theory contrasts but not all country/item cells. We therefore interpret the original 16-target result as a proof-of-concept and treat cross-country covariance variation as a boundary condition for future work.
# 
# Recommended language if the high-stakes ultimatum test shows a strong stake effect:
# 
# > The high-stakes ultimatum analysis suggests that the monetary dimension is not globally inactive. Instead, money appears inactive in low-stakes social-game and lottery contexts but becomes diagnostic when stake variation is experimentally designed to be salient. We therefore revise the "money-zero" claim as a context-specific boundary condition rather than a universal conclusion.
