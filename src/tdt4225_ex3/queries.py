import sys
from collections import defaultdict
from itertools import combinations
from pprint import pprint
from typing import TYPE_CHECKING

from tdt4225_ex3.db_connector import DbConnector

if TYPE_CHECKING:
    from pymongo.synchronous.database import Database


def task_1(db: Database):
    return db.movies.aggregate(
        [
            {"$unwind": "$crew"},
            {"$match": {"crew.job": "Director"}},
            {
                "$group": {
                    "_id": "$crew.id",
                    "name": {"$first": "$crew.name"},
                    "median_revenue": {
                        "$median": {"input": "$revenue", "method": "approximate"}
                    },
                    "movie_count": {"$sum": 1},
                    "vote_average": {"$avg": "$vote_average"},
                }
            },
            {"$match": {"movie_count": {"$gte": 5}}},
            {"$sort": {"median_revenue": -1}},
            {"$limit": 10},
        ]
    )


def task_2(db: Database):
    movies = db.movies.find({}, {"vote_average": 1, "cast.id": 1, "cast.name": 1})

    id_to_name: dict[int, str] = {}
    pair_counts: dict[tuple[int, int], int] = defaultdict(int)
    pair_ratings: dict[tuple[int, int], list[float]] = defaultdict(list)

    for movie in movies:
        for actor in movie["cast"]:
            id_to_name[actor["id"]] = actor["name"]

        # sorted makes sure that we dont store pairs "a,b" and "b,a" as different pairs
        for pair in combinations(sorted({actor["id"] for actor in movie["cast"]}), 2):
            pair_counts[pair] += 1
            if movie["vote_average"] is not None:
                pair_ratings[pair].append(movie["vote_average"])

    result = [
        {
            "actor_a": id_to_name[a],
            "actor_b": id_to_name[b],
            "co_appearances": count,
            "avg_vote_average": sum(pair_ratings[a, b]) / len(pair_ratings[a, b])
            if pair_ratings[a, b]
            else None,
        }
        for (a, b), count in pair_counts.items()
        if count >= 3
    ]
    return sorted(result, key=lambda r: r["co_appearances"], reverse=True)


def task_3(db: Database):
    return db.movies.aggregate(
        [
            {"$project": {"genres": "$genres.name", "cast.id": 1, "cast.name": 1}},
            {"$unwind": "$cast"},
            {"$unwind": {"path": "$genres", "preserveNullAndEmptyArrays": True}},
            {
                "$group": {
                    "_id": "$cast.id",
                    "name": {"$first": "$cast.name"},
                    "movies": {"$addToSet": "$_id"},
                    "genres": {"$addToSet": "$genres"},
                }
            },
            {"$match": {"$expr": {"$gte": [{"$size": "$movies"}, 10]}}},
            {
                "$project": {
                    "name": 1,
                    "genre_count": {"$size": "$genres"},
                    "example_genres": {"$slice": ["$genres", 5]},
                }
            },
            {"$sort": {"genre_count": -1}},
            {"$limit": 10},
        ]
    )


def task_4(db: Database):
    return db.movies.aggregate(
        [
            {"$match": {"belongs_to_collection": {"$ne": None}}},
            {
                "$group": {
                    "_id": "$belongs_to_collection.id",
                    "name": {"$first": "$belongs_to_collection.name"},
                    "total_revenue": {"$sum": "$revenue"},
                    "movie_count": {"$sum": 1},
                    "median_vote_average": {
                        "$median": {"input": "$vote_average", "method": "approximate"}
                    },
                    "earliest_release": {"$min": "$release_date"},
                    "latest_release": {"$max": "$release_date"},
                }
            },
            {"$match": {"movie_count": {"$gte": 3}}},
            {"$sort": {"total_revenue": -1}},
            {"$limit": 10},
        ]
    )


def task_5(db: Database):
    return db.movies.aggregate(
        [
            {
                "$match": {
                    "release_date": {"$ne": None},
                    "$expr": {"$gt": [{"$size": "$genres"}, 0]},
                }
            },
            {
                "$group": {
                    "_id": {
                        "decade": {
                            "$subtract": [
                                {"$year": "$release_date"},
                                {"$mod": [{"$year": "$release_date"}, 10]},
                            ]
                        },
                        "primary_genre": {"$first": "$genres.name"},
                    },
                    "median_runtime": {
                        "$median": {"input": "$runtime", "method": "approximate"}
                    },
                    "movie_count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "decade": "$_id.decade",
                    "primary_genre": "$_id.primary_genre",
                    "median_runtime": 1,
                    "movie_count": 1,
                    "_id": 0,
                }
            },
            {"$sort": {"decade": 1, "median_runtime": -1}},
        ]
    )


def task_6(db: Database):
    raise NotImplementedError


def task_7(db: Database):
    raise NotImplementedError


def task_8(db: Database):
    raise NotImplementedError


def task_9(db: Database):
    raise NotImplementedError


def task_10(db: Database):
    raise NotImplementedError


TASKS = {
    1: task_1,
    2: task_2,
    3: task_3,
    4: task_4,
    5: task_5,
    6: task_6,
    7: task_7,
    8: task_8,
    9: task_9,
    10: task_10,
}


def main():
    numbers = [int(n) for n in sys.argv[1:]] or TASKS

    connection = DbConnector()
    try:
        for n in numbers:
            print(f"\nTask {n}:")
            f = TASKS[n]
            pprint(list(f(connection.db)))
    finally:
        connection.close_connection()
