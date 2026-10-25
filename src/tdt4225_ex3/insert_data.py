import sys
from typing import TYPE_CHECKING

from tdt4225_ex3.data_cleaning import build_movies, get_cleaned_data
from tdt4225_ex3.db_connector import DbConnector

if TYPE_CHECKING:
    from polars import DataFrame
    from pymongo.synchronous.collection import Collection


BATCH_SIZE = 100_000


def insert_batches(collection: Collection, df: DataFrame):
    # Converting all ratings to dicts at once uses too much memory
    for batch in df.iter_slices(BATCH_SIZE):
        collection.insert_many(batch.to_dicts(), ordered=False)


def main():
    small = "--small" in sys.argv
    datasets = get_cleaned_data()
    ratings = datasets["ratings_small" if small else "ratings"]

    connection = DbConnector()
    db = connection.db
    try:
        print("Dropping existing collections")
        for name in ("movies", "ratings"):
            db.drop_collection(name)

        print("Building movies list")
        movies = build_movies(datasets)

        print("Inserting movies")
        db.movies.insert_many(movies, ordered=False)
        print(f"Inserted {len(movies)} movies")

        print("Inserting ratings")
        insert_batches(db.ratings, ratings)
        print(f"Inserted {ratings.height} ratings")

        print("Creating indexes")
        # Ratings reference movies through the MovieLens id
        db.movies.create_index("movielens_ids")
        db.ratings.create_index("userId")
        db.ratings.create_index("movieId")
        # Text search over overview and tagline
        db.movies.create_index([("overview", "text"), ("tagline", "text")])
    finally:
        connection.close_connection()


if __name__ == "__main__":
    main()
