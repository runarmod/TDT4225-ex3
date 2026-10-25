import sys
from pprint import pprint
from typing import TYPE_CHECKING

from tdt4225_ex3.db_connector import DbConnector

if TYPE_CHECKING:
    from pymongo.synchronous.database import Database


def task_1(db: Database):
    raise NotImplementedError


def task_2(db: Database):
    raise NotImplementedError


def task_3(db: Database):
    raise NotImplementedError


def task_4(db: Database):
    raise NotImplementedError


def task_5(db: Database):
    raise NotImplementedError


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
