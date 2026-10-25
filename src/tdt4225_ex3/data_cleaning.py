import csv
import io
import os
from pathlib import Path

import polars as pl


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

    return {
        "credits": pl.read_csv(data_dir / "credits.csv"),
        "keywords": pl.read_csv(data_dir / "keywords.csv"),
        "links_small": pl.read_csv(data_dir / "links_small.csv"),
        "links": pl.read_csv(data_dir / "links.csv"),
        "movies_metadata": movies_metadata,
        "ratings_small": pl.read_csv(data_dir / "ratings_small.csv"),
        "ratings": pl.read_csv(data_dir / "ratings.csv"),
    }


def get_cleaned_data():
    datasets = get_data()
    datasets = {k: v.unique() for k, v in datasets.items()}

    datasets["movies_metadata"] = (
        datasets["movies_metadata"]
        .sort("vote_count", "popularity", descending=True)
        .unique("id", keep="first", maintain_order=True)
    )
    # 0 means unknown, so replace it with null
    datasets["movies_metadata"] = datasets["movies_metadata"].with_columns(
        pl.when(pl.col(col) != 0).then(pl.col(col)).alias(col)
        for col in ("budget", "revenue", "runtime")
    )
    # An average of no votes is meaningless
    datasets["movies_metadata"] = datasets["movies_metadata"].with_columns(
        pl.when(pl.col("vote_count") > 0)
        .then(pl.col("vote_average"))
        .alias("vote_average")
    )
    # Datetime, not date, since pymongo can only store datetimes
    datasets["movies_metadata"] = datasets["movies_metadata"].with_columns(
        pl.col("release_date").str.to_datetime("%Y-%m-%d")
    )
    for name in ("ratings", "ratings_small"):
        datasets[name] = datasets[name].with_columns(pl.from_epoch("timestamp"))

    datasets["credits"] = (
        datasets["credits"]
        .sort(pl.col("crew").str.count_matches("'credit_id'"), descending=True)
        .unique("id", keep="first", maintain_order=True)
    )
    return datasets
