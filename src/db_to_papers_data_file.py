import sqlite3
import json
from src.constants import *

with sqlite3.connect(DATABASE_FILE_NAME) as con:
    all_json_rows = []
    for year in range(2013, 2022 + 1):
        cur = con.cursor()
        cur.execute(
            f"SELECT * FROM papers where papers.year = {year} order by citation_count desc limit 20"
        )
        rows = cur.fetchall()
        json_rows = [
            {"url": url, "year": year, "title": title, "cites": cites}
            for url, year, title, cites in rows
        ]
        all_json_rows.extend(json_rows)
    with open("_data/papers.json", "w") as f:
        json.dump(all_json_rows, f)
    con.commit()
