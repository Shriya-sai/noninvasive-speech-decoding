#!/usr/bin/env python3
"""Download and verify the frozen multi-day QC subset into git-annex."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
import subprocess
import tomllib
from pathlib import Path
from urllib.parse import quote


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def materialize(
    dataset_root: Path,
    relative: str,
    expected_bytes: int,
    expected_sha256: str,
    accession: str,
) -> str:
    link = dataset_root / relative
    if not link.is_symlink():
        raise ValueError(f"expected git-annex symlink: {link}")
    destination = (link.parent / os.readlink(link)).resolve(strict=False)
    if destination.is_file():
        if destination.stat().st_size != expected_bytes:
            raise ValueError(f"wrong existing size: {link}")
        if sha256(destination) != expected_sha256:
            raise ValueError(f"wrong existing checksum: {link}")
        return "verified-existing"

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(f"{destination.name}.partial")
    url = f"https://s3.amazonaws.com/openneuro.org/{accession}/{quote(relative)}"
    subprocess.run(
        [
            "curl",
            "-fL",
            "--silent",
            "--show-error",
            "--retry",
            "4",
            "-C",
            "-",
            "-o",
            str(partial),
            url,
        ],
        check=True,
    )
    if partial.stat().st_size != expected_bytes:
        raise ValueError(f"downloaded size mismatch: {relative}")
    if sha256(partial) != expected_sha256:
        raise ValueError(f"downloaded checksum mismatch: {relative}")
    os.replace(partial, destination)
    return "downloaded-and-verified"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset_root", type=Path)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/qc_calibration_subset.toml"),
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    config = tomllib.loads(args.config.read_text())
    accession = config["selection"]["dataset_accession"]
    if args.workers < 1:
        raise ValueError("workers must be positive")
    jobs = [
        (run, kind)
        for run in config["runs"]
        for kind in ("eeg", "audio")
    ]
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                materialize,
                args.dataset_root,
                run[kind],
                run[f"{kind}_bytes"],
                run[f"{kind}_sha256"],
                accession,
            ): (run, kind)
            for run, kind in jobs
        }
        for future in as_completed(futures):
            run, kind = futures[future]
            print(run["id"], kind, future.result(), flush=True)


if __name__ == "__main__":
    main()
