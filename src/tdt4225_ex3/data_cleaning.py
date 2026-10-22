import csv
import io
import os
from collections import namedtuple
from pathlib import Path

import polars as pl

Dataset = namedtuple(
    "dataset",
    [
        "credits",
        "keywords",
        "links_small",
        "links",
        "movies_metadata",
        "ratings_small",
        "ratings",
    ],
)


def read_csv_merging_split_rows(path):
    """Read a CSV where unquoted newlines split some records into too-short rows."""
    with open(path, encoding="utf-8", newline="") as f:
        header, *rows = csv.reader(f)

    merged = []
    for row in rows:
        # If the previous row doesn't have enough columns, treat the current row as extention of the previous
        if merged and len(merged[-1]) < len(header):
            merged[-1][-1] += "\n" + row[0]
            merged[-1] += row[1:]
        else:
            merged.append(row)

    buf = io.StringIO()
    csv.writer(buf).writerows([header, *merged])
    buf.seek(0)
    return pl.read_csv(buf)


def get_data():
    data_dir = Path(os.path.abspath("")).resolve().parents[1] / "data"

    # Metadata had mistakes in the lines
    movies_metadata = read_csv_merging_split_rows(data_dir / "movies_metadata.csv")

    return Dataset(
        credits=pl.read_csv(data_dir / "credits.csv"),
        keywords=pl.read_csv(data_dir / "keywords.csv"),
        links_small=pl.read_csv(data_dir / "links_small.csv"),
        links=pl.read_csv(data_dir / "links.csv"),
        movies_metadata=movies_metadata,
        ratings_small=pl.read_csv(data_dir / "ratings_small.csv"),
        ratings=pl.read_csv(data_dir / "ratings.csv"),
    )
