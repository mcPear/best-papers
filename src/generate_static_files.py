import sqlite3
import json
from src.constants import *

with sqlite3.connect(DATABASE_FILE_NAME) as con:
    for year in range(2013, 2022):
        cur = con.cursor()
        cur.execute(
            f"SELECT * FROM papers where strftime('%Y', papers.published) = '{year}' order by citation_count desc limit 20"
        )
        rows = cur.fetchall()
        json_rows = [
            {"url": url, "inserted_at": inserted_at, "title": title, "cites": cites}
            for url, inserted_at, title, cites in rows
        ]
        with open("_data/papers.json", "w") as f:
            json.dump(json_rows, f)
        con.commit()
