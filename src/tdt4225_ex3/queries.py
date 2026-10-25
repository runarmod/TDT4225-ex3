import heapq
import sys
from collections import defaultdict
from itertools import combinations
from pprint import pprint
from typing import TYPE_CHECKING

from pymongo.command_cursor import CommandCursor

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
            {
                "$project": {
                    "_id": 0,
                    "director_id": "$_id",
                    "name": 1,
                    "median_revenue": 1,
                    "movie_count": 1,
                    "vote_average": 1,
                }
            },
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
                    "_id": 0,
                    "actor_id": "$_id",
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
            {
                "$project": {
                    "_id": 0,
                    "collection_id": "$_id",
                    "name": 1,
                    "total_revenue": 1,
                    "movie_count": 1,
                    "median_vote_average": 1,
                    "earliest_release": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$earliest_release",
                        }
                    },
                    "latest_release": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$latest_release",
                        }
                    },
                }
            },
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
    return db.movies.aggregate(
        [
            {"$match": {"release_date": {"$ne": None}}},
            {
                "$project": {
                    "decade": {
                        "$subtract": [
                            {"$year": "$release_date"},
                            {"$mod": [{"$year": "$release_date"}, 10]},
                        ]
                    },
                    "known": {
                        "$filter": {
                            "input": {
                                "$slice": [
                                    {
                                        "$sortArray": {
                                            "input": "$cast",
                                            "sortBy": {"order": 1},
                                        }
                                    },
                                    5,
                                ]
                            },
                            "cond": {"$in": ["$$this.gender", [1, 2]]},
                        }
                    },
                },
            },
            {"$match": {"$expr": {"$gt": [{"$size": "$known"}, 0]}}},
            {
                "$project": {
                    "decade": 1,
                    "female_proportion": {
                        "$divide": [
                            {
                                "$size": {
                                    "$filter": {
                                        "input": "$known",
                                        "cond": {"$eq": ["$$this.gender", 1]},
                                    }
                                }
                            },
                            {"$size": "$known"},
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$decade",
                    "avg_female_proportion": {"$avg": "$female_proportion"},
                    "movie_count": {"$sum": 1},
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "decade": "$_id",
                    "avg_female_proportion": 1,
                    "movie_count": 1,
                }
            },
            {"$sort": {"avg_female_proportion": -1}},
        ]
    )


def task_7(db: Database):
    return db.movies.aggregate(
        [
            # Movies matching "neo-noir" also matches on "noir", so we only need "noir"
            {"$match": {"$text": {"$search": "noir"}, "vote_count": {"$gte": 50}}},
            {
                "$project": {
                    "_id": 0,
                    "title": 1,
                    "year": {"$year": "$release_date"},
                    "vote_average": 1,
                    "vote_count": 1,
                }
            },
            {"$sort": {"vote_average": -1}},
            {"$limit": 20},
        ]
    )


def task_8(db: Database):
    def uniquePeople(array):
        # One {id, name} per person, so a director or actor listed twice in a movie counts once
        return {
            "$setUnion": [
                {
                    "$map": {
                        "input": array,
                        "in": {"id": "$$this.id", "name": "$$this.name"},
                    }
                }
            ]
        }

    return db.movies.aggregate(
        [
            {"$match": {"vote_count": {"$gte": 100}}},
            {
                "$project": {
                    "vote_average": 1,
                    "revenue": 1,
                    "directors": uniquePeople(
                        {
                            "$filter": {
                                "input": "$crew",
                                "cond": {"$eq": ["$$this.job", "Director"]},
                            }
                        }
                    ),
                    "actors": uniquePeople("$cast"),
                }
            },
            {"$unwind": "$directors"},
            {"$unwind": "$actors"},
            {
                "$group": {
                    "_id": {"director": "$directors.id", "actor": "$actors.id"},
                    "director": {"$first": "$directors.name"},
                    "actor": {"$first": "$actors.name"},
                    "movie_count": {"$sum": 1},
                    "mean_vote_average": {"$avg": "$vote_average"},
                    "mean_revenue": {"$avg": "$revenue"},
                }
            },
            {"$match": {"movie_count": {"$gte": 3}}},
            {"$sort": {"mean_vote_average": -1}},
            {"$limit": 20},
            {
                "$project": {
                    "_id": 0,
                    "director": 1,
                    "actor": 1,
                    "movie_count": 1,
                    "mean_vote_average": 1,
                    "mean_revenue": 1,
                }
            },
        ]
    )


def task_9(db: Database):
    return db.movies.aggregate(
        [
            {
                "$match": {
                    "original_language": {"$ne": "en"},
                    "$or": [
                        {"production_countries.iso_3166_1": "US"},
                        {"production_companies.name": "United States"},
                    ],
                }
            },
            {"$sort": {"popularity": -1}},
            {
                "$group": {
                    "_id": "$original_language",
                    "count": {"$sum": 1},
                    "example_title": {"$first": "$title"},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {
                "$project": {
                    "_id": 0,
                    "original_language": "$_id",
                    "count": 1,
                    "example_title": 1,
                }
            },
        ]
    )


def task_10(db: Database):
    genres: dict[int, set[int]] = defaultdict(set)
    for movie in db.movies.find({}, {"movielens_ids": 1, "genres.id": 1}):
        for movielens_id in movie["movielens_ids"]:
            genres[movielens_id] |= {g["id"] for g in movie["genres"]}

    users = db.ratings.aggregate(
        [
            {
                "$group": {
                    "_id": "$userId",
                    "ratings_count": {"$sum": 1},
                    "std": {"$stdDevPop": "$rating"},
                    "movies": {"$push": "$movieId"},
                }
            },
            {"$match": {"ratings_count": {"$gte": 20}}},
            {
                "$project": {
                    "_id": 0,
                    "userId": "$_id",
                    "movies": 1,
                    "ratings_count": 1,
                    "variance": {"$pow": ["$std", 2]},
                }
            },
        ]
    )
    user_stats = [
        {
            "userId": user["userId"],
            "ratings_count": user["ratings_count"],
            "variance": user["variance"],
            "distinct_genres": len(
                {genre for m in user["movies"] for genre in genres.get(m, ())}
            ),
        }
        for user in users
    ]

    return {
        "most_genre_diverse": heapq.nlargest(
            10, user_stats, key=lambda s: s["distinct_genres"]
        ),
        "highest_variance": heapq.nlargest(10, user_stats, key=lambda s: s["variance"]),
    }


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
            results = TASKS[n](connection.db)
            if isinstance(results, CommandCursor):
                pprint(list(results))
            else:
                pprint(results)
    finally:
        connection.close_connection()
