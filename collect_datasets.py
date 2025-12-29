#!/usr/bin/env python3
"""
QND Dataset Collector
Downloads and prepares datasets for Quantum Normative Dynamics experiments.

DISK SPACE REQUIREMENTS:
========================
Dataset                          Size (approx)
-------------------------------------------------
AITA Reddit (HuggingFace)        ~500 MB (270K posts)
Jigsaw Toxic Comments            ~100 MB (160K comments)
Scruples Anecdotes              ~50 MB (32K anecdotes)
Scruples Dilemmas               ~10 MB (10K dilemmas)
Hendrycks ETHICS                ~20 MB (multi-task)
-------------------------------------------------
TOTAL                           ~700 MB compressed
                                ~1.5 GB extracted

ADDITIONAL OPTIONAL:
MIT Moral Machine               ~200 MB (sampled)
Social Chemistry 101            ~100 MB

Usage:
    python collect_datasets.py --all           # Download everything
    python collect_datasets.py --aita          # Just AITA
    python collect_datasets.py --minimal       # Small test set only
    python collect_datasets.py --list          # Show available datasets
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import urllib.request
import zipfile
import gzip
import shutil

# Try to import optional dependencies
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas not installed. Install with: pip install pandas")

try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    print("Warning: datasets not installed. Install with: pip install datasets")


# ============================================================================
# DATASET REGISTRY
# ============================================================================

DATASETS = {
    "aita_huggingface": {
        "name": "Reddit AITA (HuggingFace)",
        "description": "270K AITA posts with verdicts (2013-2023)",
        "source": "huggingface",
        "hf_path": "OsamaBsher/AITA-Reddit-Dataset",
        "size_mb": 500,
        "records": 270709,
        "columns": ["title", "text", "verdict", "comment1", "comment2", "score"],
        "best_for": ["order_effects", "interference", "superposition"],
        "license": "Reddit API Terms"
    },
    "aita_binary": {
        "name": "Reddit AITA Binary (HuggingFace)",
        "description": "11K AITA posts, binary classification",
        "source": "huggingface",
        "hf_path": "jeanong2/AITA-datasets",
        "size_mb": 20,
        "records": 16872,
        "columns": ["text", "label"],
        "best_for": ["quick_testing", "baseline"],
        "license": "Unknown"
    },
    "jigsaw_toxic": {
        "name": "Jigsaw Toxic Comments",
        "description": "160K Wikipedia comments labeled for toxicity",
        "source": "huggingface",
        "hf_path": "google/jigsaw_toxicity_pred",
        "size_mb": 100,
        "records": 159571,
        "columns": ["text", "toxic", "severe_toxic", "obscene", "threat", "insult", "identity_hate"],
        "best_for": ["content_moderation", "multi_label"],
        "license": "CC0 / CC-SA-3.0"
    },
    "scruples_anecdotes": {
        "name": "Scruples Anecdotes",
        "description": "32K real-life ethical anecdotes with judgments",
        "source": "url",
        "url": "https://storage.googleapis.com/ai2-mosaic-public/projects/scruples/v1.0/data/anecdotes.tar.gz",
        "size_mb": 50,
        "records": 32000,
        "columns": ["text", "binarized_label", "label_distribution"],
        "best_for": ["interference", "superposition", "entanglement"],
        "license": "Research Only"
    },
    "scruples_dilemmas": {
        "name": "Scruples Dilemmas",
        "description": "10K paired action dilemmas",
        "source": "url",
        "url": "https://storage.googleapis.com/ai2-mosaic-public/projects/scruples/v1.0/data/dilemmas.tar.gz",
        "size_mb": 10,
        "records": 10000,
        "columns": ["action1", "action2", "label"],
        "best_for": ["interference", "comparison"],
        "license": "Research Only"
    },
    "hendrycks_ethics": {
        "name": "Hendrycks ETHICS Benchmark",
        "description": "Multi-task ethics benchmark (justice, deontology, virtue, etc.)",
        "source": "huggingface",
        "hf_path": "hendrycks/ethics",
        "size_mb": 20,
        "records": 130000,
        "columns": ["varies by subset"],
        "best_for": ["multi_framework", "interference"],
        "license": "MIT"
    },
    "reddit_ethics": {
        "name": "Reddit Ethics (Structured)",
        "description": "AITA posts with structured ethical analysis",
        "source": "huggingface",
        "hf_path": "agentlans/reddit-ethics",
        "size_mb": 30,
        "records": 1000,
        "columns": ["text", "utilitarianism", "deontology", "virtue_ethics", "questions"],
        "best_for": ["interference", "multi_framework"],
        "license": "Unknown"
    }
}


# ============================================================================
# DOWNLOAD FUNCTIONS
# ============================================================================

class DatasetCollector:
    def __init__(self, output_dir: str = "./qnd_datasets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manifest = {"downloaded": [], "timestamp": None, "total_size_mb": 0}
        self.manifest_path = self.output_dir / "manifest.json"
        self._load_manifest()
    
    def _load_manifest(self):
        if self.manifest_path.exists():
            with open(self.manifest_path) as f:
                self.manifest = json.load(f)
    
    def _save_manifest(self):
        self.manifest["timestamp"] = datetime.now().isoformat()
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _progress_hook(self, count, block_size, total_size):
        """Progress callback for urllib"""
        percent = int(count * block_size * 100 / total_size) if total_size > 0 else 0
        bar = '█' * (percent // 5) + '░' * (20 - percent // 5)
        sys.stdout.write(f'\r  [{bar}] {percent}%')
        sys.stdout.flush()
    
    def download_huggingface(self, dataset_id: str, config: dict) -> Optional[Path]:
        """Download dataset from HuggingFace"""
        if not HAS_DATASETS:
            print(f"  ERROR: 'datasets' library not installed")
            print(f"  Run: pip install datasets")
            return None
        
        hf_path = config["hf_path"]
        output_path = self.output_dir / f"{dataset_id}.parquet"
        
        if output_path.exists():
            print(f"  Already exists: {output_path}")
            return output_path
        
        print(f"  Downloading from HuggingFace: {hf_path}")
        try:
            # Load dataset
            if dataset_id == "hendrycks_ethics":
                # This one has multiple configs
                ds = load_dataset(hf_path, "commonsense", trust_remote_code=True)
            else:
                ds = load_dataset(hf_path, trust_remote_code=True)
            
            # Convert to pandas and save
            if "train" in ds:
                df = ds["train"].to_pandas()
            else:
                # Some datasets don't have train split
                first_split = list(ds.keys())[0]
                df = ds[first_split].to_pandas()
            
            # Save as parquet (efficient)
            df.to_parquet(output_path)
            print(f"\n  Saved {len(df)} records to {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"\n  ERROR downloading {hf_path}: {e}")
            return None
    
    def download_url(self, dataset_id: str, config: dict) -> Optional[Path]:
        """Download dataset from URL"""
        url = config["url"]
        filename = url.split("/")[-1]
        download_path = self.output_dir / filename
        extract_dir = self.output_dir / dataset_id
        
        if extract_dir.exists():
            print(f"  Already exists: {extract_dir}")
            return extract_dir
        
        print(f"  Downloading: {url}")
        try:
            urllib.request.urlretrieve(url, download_path, self._progress_hook)
            print()  # Newline after progress
            
            # Extract
            print(f"  Extracting...")
            if filename.endswith('.tar.gz'):
                import tarfile
                with tarfile.open(download_path, 'r:gz') as tar:
                    tar.extractall(extract_dir)
            elif filename.endswith('.zip'):
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif filename.endswith('.gz'):
                with gzip.open(download_path, 'rb') as f_in:
                    output_file = extract_dir / filename[:-3]
                    extract_dir.mkdir(exist_ok=True)
                    with open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            # Clean up download
            download_path.unlink()
            print(f"  Extracted to {extract_dir}")
            
            return extract_dir
            
        except Exception as e:
            print(f"\n  ERROR downloading {url}: {e}")
            if download_path.exists():
                download_path.unlink()
            return None
    
    def download_dataset(self, dataset_id: str) -> Optional[Path]:
        """Download a single dataset"""
        if dataset_id not in DATASETS:
            print(f"Unknown dataset: {dataset_id}")
            return None
        
        config = DATASETS[dataset_id]
        print(f"\n{'='*60}")
        print(f"Downloading: {config['name']}")
        print(f"Description: {config['description']}")
        print(f"Expected size: ~{config['size_mb']} MB")
        print(f"{'='*60}")
        
        source = config["source"]
        if source == "huggingface":
            path = self.download_huggingface(dataset_id, config)
        elif source == "url":
            path = self.download_url(dataset_id, config)
        else:
            print(f"  Unknown source type: {source}")
            return None
        
        if path:
            self.manifest["downloaded"].append({
                "id": dataset_id,
                "name": config["name"],
                "path": str(path),
                "size_mb": config["size_mb"],
                "timestamp": datetime.now().isoformat()
            })
            self.manifest["total_size_mb"] += config["size_mb"]
            self._save_manifest()
        
        return path
    
    def download_all(self, dataset_ids: Optional[List[str]] = None):
        """Download multiple datasets"""
        if dataset_ids is None:
            dataset_ids = list(DATASETS.keys())
        
        total_size = sum(DATASETS[d]["size_mb"] for d in dataset_ids)
        print(f"\n{'#'*60}")
        print(f"QND Dataset Collection")
        print(f"Datasets to download: {len(dataset_ids)}")
        print(f"Estimated total size: ~{total_size} MB")
        print(f"Output directory: {self.output_dir}")
        print(f"{'#'*60}")
        
        results = {}
        for dataset_id in dataset_ids:
            path = self.download_dataset(dataset_id)
            results[dataset_id] = path
        
        # Summary
        print(f"\n{'='*60}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*60}")
        success = sum(1 for p in results.values() if p is not None)
        print(f"Successful: {success}/{len(dataset_ids)}")
        print(f"Total size: ~{self.manifest['total_size_mb']} MB")
        print(f"Manifest saved to: {self.manifest_path}")
        
        return results


# ============================================================================
# DATA PREPARATION FOR QND
# ============================================================================

def prepare_aita_for_qnd(parquet_path: Path, output_path: Path, sample_size: int = 1000):
    """Prepare AITA data for QND experiments"""
    if not HAS_PANDAS:
        print("pandas required for data preparation")
        return None
    
    print(f"\nPreparing AITA data for QND...")
    df = pd.read_parquet(parquet_path)
    
    # Calculate ambiguity proxy from score distribution
    # Low score = more contested = higher ambiguity
    df['ambiguity'] = pd.qcut(df['score'], q=3, labels=['high', 'medium', 'low'])
    
    # Sample stratified by verdict and ambiguity
    if len(df) > sample_size:
        # Try to get balanced sample
        sampled = df.groupby(['verdict', 'ambiguity'], group_keys=False).apply(
            lambda x: x.sample(min(len(x), sample_size // 12), random_state=42)
        )
        if len(sampled) < sample_size:
            # Fill with random samples
            remaining = df[~df.index.isin(sampled.index)]
            extra = remaining.sample(min(len(remaining), sample_size - len(sampled)), random_state=42)
            sampled = pd.concat([sampled, extra])
        df = sampled
    
    # Prepare for QND format
    qnd_data = []
    for _, row in df.iterrows():
        qnd_data.append({
            "id": hashlib.md5(str(row.get('title', '') + str(row.get('text', ''))).encode()).hexdigest()[:12],
            "title": str(row.get('title', '')),
            "body": str(row.get('text', ''))[:5000],  # Truncate very long posts
            "verdict": str(row.get('verdict', 'UNKNOWN')),
            "score": int(row.get('score', 0)) if pd.notna(row.get('score')) else 0,
            "ambiguity_level": str(row.get('ambiguity', 'unknown')),
            "comment1": str(row.get('comment1', ''))[:1000] if pd.notna(row.get('comment1')) else '',
            "comment2": str(row.get('comment2', ''))[:1000] if pd.notna(row.get('comment2')) else ''
        })
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(qnd_data, f, indent=2)
    
    print(f"Saved {len(qnd_data)} posts to {output_path}")
    
    # Stats
    verdicts = pd.DataFrame(qnd_data)['verdict'].value_counts()
    print(f"\nVerdict distribution:")
    for v, c in verdicts.items():
        print(f"  {v}: {c}")
    
    return qnd_data


def prepare_scruples_for_qnd(scruples_dir: Path, output_path: Path, sample_size: int = 500):
    """Prepare Scruples data for QND experiments"""
    if not HAS_PANDAS:
        print("pandas required for data preparation")
        return None
    
    print(f"\nPreparing Scruples data for QND...")
    
    # Find the JSON files
    data_files = list(scruples_dir.rglob("*.jsonl")) + list(scruples_dir.rglob("*.json"))
    
    if not data_files:
        print(f"No data files found in {scruples_dir}")
        return None
    
    all_data = []
    for f in data_files:
        try:
            if f.suffix == '.jsonl':
                with open(f) as fp:
                    for line in fp:
                        all_data.append(json.loads(line))
            else:
                with open(f) as fp:
                    data = json.load(fp)
                    if isinstance(data, list):
                        all_data.extend(data)
        except Exception as e:
            print(f"  Error reading {f}: {e}")
    
    print(f"Loaded {len(all_data)} records from Scruples")
    
    # Convert to QND format
    qnd_data = []
    for item in all_data[:sample_size]:
        # Scruples has various formats
        text = item.get('text', item.get('title', item.get('action', '')))
        label = item.get('binarized_label', item.get('label', 'UNKNOWN'))
        
        # Map label to AITA-style verdict
        if label in [0, '0', 'WRONG']:
            verdict = "YTA"
        elif label in [1, '1', 'NOT WRONG']:
            verdict = "NTA"
        else:
            verdict = "UNKNOWN"
        
        qnd_data.append({
            "id": hashlib.md5(text.encode()).hexdigest()[:12],
            "title": text[:100] + "..." if len(text) > 100 else text,
            "body": text,
            "verdict": verdict,
            "score": 0,
            "ambiguity_level": "high",  # Scruples cases tend to be contested
            "source": "scruples"
        })
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(qnd_data, f, indent=2)
    
    print(f"Saved {len(qnd_data)} posts to {output_path}")
    return qnd_data


# ============================================================================
# MAIN
# ============================================================================

def list_datasets():
    """Print available datasets"""
    print("\n" + "=" * 70)
    print("AVAILABLE DATASETS FOR QND EXPERIMENTS")
    print("=" * 70)
    
    total_size = 0
    for dataset_id, config in DATASETS.items():
        print(f"\n{dataset_id}")
        print(f"  Name: {config['name']}")
        print(f"  Records: {config['records']:,}")
        print(f"  Size: ~{config['size_mb']} MB")
        print(f"  Best for: {', '.join(config['best_for'])}")
        print(f"  License: {config['license']}")
        total_size += config['size_mb']
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {len(DATASETS)} datasets, ~{total_size} MB")
    print(f"{'='*70}")


def create_synthetic_test_data(output_path: Path, n_samples: int = 100):
    """Create synthetic test data when downloads fail (for testing the pipeline)"""
    print(f"\nCreating synthetic test data ({n_samples} samples)...")
    
    # Based on real AITA patterns
    templates = [
        {
            "template": "AITA for {action} when my {relation} {context}?",
            "actions": ["refusing to help", "telling the truth about", "not attending", "calling out", "reporting"],
            "relations": ["sister", "brother", "mom", "dad", "friend", "coworker", "neighbor"],
            "contexts": ["asked me to lie for them", "borrowed money and didn't pay back", 
                        "made a rude comment", "excluded me from an event", "damaged my property"]
        }
    ]
    
    import random
    random.seed(42)
    
    verdicts = ["NTA", "YTA", "ESH", "NAH"]
    verdict_weights = [0.5, 0.25, 0.15, 0.1]  # NTA most common
    ambiguity_levels = ["low", "medium", "high"]
    
    data = []
    for i in range(n_samples):
        t = templates[0]
        action = random.choice(t["actions"])
        relation = random.choice(t["relations"])
        context = random.choice(t["contexts"])
        
        title = f"AITA for {action} when my {relation} {context}?"
        body = f"""I ({random.randint(20,45)}{random.choice(['M','F'])}) have been dealing with a situation 
with my {relation}. Recently, they {context}. I decided to {action.replace('refusing to help', 'refuse to help')}.

Now my family thinks I'm being too harsh, but I feel like I had to set a boundary. 
My {relation} says I'm overreacting and that I should just let it go.

Some additional context: This isn't the first time something like this has happened. 
I've tried talking to them about it before but nothing changed.

So Reddit, AITA?"""
        
        # Assign verdict with weights
        verdict = random.choices(verdicts, weights=verdict_weights)[0]
        
        # ESH and NAH cases are more ambiguous
        if verdict in ["ESH", "NAH"]:
            ambiguity = "high"
        elif verdict == "YTA":
            ambiguity = random.choice(["medium", "high"])
        else:
            ambiguity = random.choice(["low", "medium"])
        
        data.append({
            "id": f"synthetic_{i:04d}",
            "title": title,
            "body": body,
            "verdict": verdict,
            "score": random.randint(100, 10000),
            "num_comments": random.randint(50, 500),
            "ambiguity_level": ambiguity,
            "source": "synthetic"
        })
    
    # Save
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved {len(data)} synthetic samples to {output_path}")
    
    # Stats
    verdict_counts = {}
    for d in data:
        v = d["verdict"]
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    
    print("\nVerdict distribution:")
    for v, c in sorted(verdict_counts.items()):
        print(f"  {v}: {c}")
    
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Download datasets for QND experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python collect_datasets.py --list              # Show available datasets
    python collect_datasets.py --minimal           # Small test set (~50 MB)
    python collect_datasets.py --aita              # Just AITA data (~500 MB)
    python collect_datasets.py --all               # Everything (~700 MB)
    python collect_datasets.py --prepare           # Download and prepare for QND
        """
    )
    
    parser.add_argument("--list", action="store_true", help="List available datasets")
    parser.add_argument("--all", action="store_true", help="Download all datasets")
    parser.add_argument("--minimal", action="store_true", help="Download minimal test set")
    parser.add_argument("--aita", action="store_true", help="Download AITA datasets only")
    parser.add_argument("--ethics", action="store_true", help="Download ethics benchmarks only")
    parser.add_argument("--prepare", action="store_true", help="Also prepare data for QND format")
    parser.add_argument("--output-dir", type=str, default="./qnd_datasets", help="Output directory")
    parser.add_argument("--sample-size", type=int, default=1000, help="Sample size for QND preparation")
    parser.add_argument("--dataset", type=str, help="Download specific dataset by ID")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic test data (no network required)")
    parser.add_argument("--synthetic-size", type=int, default=100, help="Number of synthetic samples")
    
    args = parser.parse_args()
    
    # Handle synthetic data generation
    if args.synthetic:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        create_synthetic_test_data(output_dir / "qnd_synthetic_data.json", args.synthetic_size)
        print(f"\n✓ Synthetic data ready for testing!")
        print(f"  Run: python qnd_aita_experiment.py --data-file {output_dir}/qnd_synthetic_data.json")
        return
    
    if args.list:
        list_datasets()
        return
    
    collector = DatasetCollector(args.output_dir)
    
    # Determine which datasets to download
    if args.dataset:
        datasets_to_download = [args.dataset]
    elif args.minimal:
        datasets_to_download = ["aita_binary"]
    elif args.aita:
        datasets_to_download = ["aita_huggingface", "aita_binary"]
    elif args.ethics:
        datasets_to_download = ["hendrycks_ethics", "reddit_ethics", "scruples_anecdotes"]
    elif args.all:
        datasets_to_download = list(DATASETS.keys())
    else:
        # Default: reasonable starting set
        datasets_to_download = ["aita_huggingface", "jigsaw_toxic"]
    
    # Download
    results = collector.download_all(datasets_to_download)
    
    # Prepare for QND if requested
    if args.prepare:
        print("\n" + "#" * 60)
        print("PREPARING DATA FOR QND EXPERIMENTS")
        print("#" * 60)
        
        output_dir = Path(args.output_dir)
        
        # Prepare AITA
        aita_path = output_dir / "aita_huggingface.parquet"
        if aita_path.exists():
            prepare_aita_for_qnd(
                aita_path,
                output_dir / "qnd_aita_prepared.json",
                args.sample_size
            )
        
        # Prepare Scruples
        scruples_dir = output_dir / "scruples_anecdotes"
        if scruples_dir.exists():
            prepare_scruples_for_qnd(
                scruples_dir,
                output_dir / "qnd_scruples_prepared.json",
                args.sample_size
            )
        
        print(f"\n✓ QND-ready data saved to {output_dir}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("""
1. Run QND experiment on downloaded data:
   python qnd_aita_experiment.py --data-file qnd_datasets/qnd_aita_prepared.json

2. Or use HuggingFace directly in your code:
   from datasets import load_dataset
   ds = load_dataset("OsamaBsher/AITA-Reddit-Dataset")

3. Check the manifest for what was downloaded:
   cat qnd_datasets/manifest.json
    """)


if __name__ == "__main__":
    main()
