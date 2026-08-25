#!/usr/bin/env python3
"""Download IMDb's public title basics dataset atomically."""

from __future__ import annotations

import argparse
import os
import tempfile
import urllib.request
from pathlib import Path


URL = "https://datasets.imdbws.com/title.basics.tsv.gz"


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the IMDb title basics dataset")
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--url", default=URL, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.dataset_dir.mkdir(parents=True, exist_ok=True)
    destination = args.dataset_dir / "title.basics.tsv.gz"
    fd, temp_name = tempfile.mkstemp(prefix=".title.basics.", suffix=".tmp", dir=args.dataset_dir)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with urllib.request.urlopen(args.url, timeout=120) as response, temp.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        os.replace(temp, destination)
    finally:
        temp.unlink(missing_ok=True)
    print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
