import ast
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


def parse(value):
    """Parse a Python-literal json column. Missing values become an empty list."""
    return ast.literal_eval(value) if value else []


def build_movies(datasets: dict[str, pl.DataFrame]):
    credits = {row["id"]: row for row in datasets["credits"].iter_rows(named=True)}
    keywords = {
        row["id"]: row["keywords"] for row in datasets["keywords"].iter_rows(named=True)
    }

    # links maps tmdbId to the MovieLens movieId used in ratings. A few movies have more than one
    movielens_ids = dict(
        datasets["links"]
        .drop_nulls("tmdbId")
        .group_by("tmdbId")
        .agg("movieId")
        .iter_rows()
    )

    movies = []
    for m in datasets["movies_metadata"].iter_rows(named=True):
        movie_id = m.pop("id")
        credit = credits.get(movie_id, {})
        for col in (
            "genres",
            "production_companies",
            "production_countries",
            "spoken_languages",
        ):
            m[col] = parse(m[col])

        movies.append(
            {
                "_id": movie_id,
                **m,
                "belongs_to_collection": parse(m["belongs_to_collection"]) or None,
                "keywords": parse(keywords.get(movie_id)),
                "cast": sorted(parse(credit.get("cast")), key=lambda c: c["order"]),
                "crew": parse(credit.get("crew")),
                "movielens_ids": movielens_ids.get(movie_id, []),
            }
        )
    return movies
