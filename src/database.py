import sqlite3
from os import environ


def create_connection():
    return sqlite3.connect(environ["DATABASE_FILE_NAME"])


def create_table(connection):
    cur = connection.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS papers (id text PRIMARY KEY, year int, title text, citation_count int)"""
    )
    connection.commit()


def execute_many(sql, records):
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.executemany(sql, records)
        connection.commit()


def escape_string(text):
    return text.replace("'", "''")


def unescape_string(text):
    return text.replace("''", "'")


def insert_or_replace(papers):
    insert_sql = f"INSERT OR REPLACE INTO papers VALUES (?, ?, ?, ?)"
    records = [
        (paper["id"], paper["year"], escape_string(paper["title"]), None)
        for paper in papers
    ]

    execute_many(insert_sql, records)


def update_citation_count(papers):
    update_sql = "UPDATE papers SET citation_count = ? WHERE id = ?"
    records = [(paper["citationCount"], paper["id"]) for paper in papers]

    execute_many(update_sql, records)


def select_papers(columns=["id", "title"]):
    with create_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(f"SELECT {', '.join(columns)} FROM papers")
        tuples = cursor.fetchall()
        return [dict(zip(columns, tuple)) for tuple in tuples]
