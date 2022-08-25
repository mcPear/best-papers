import sqlite3
import json
from src.constants import *

with sqlite3.connect(DATABASE_FILE_NAME) as con:
    for scope, name in [
        ("= 2013", 2013),
        ("= 2014", 2014),
        ("= 2015", 2015),
        ("= 2016", 2016),
        ("= 2017", 2017),
        ("= 2018", 2018),
        ("= 2019", 2019),
        ("= 2020", 2020),
        ("= 2021", 2021),
        ("= 2022", 2022),
        (">= 2021", 2),
        (">= 2018", 5),
        (">= 2013", "all"),
    ]:  # TODO implement it dependent on the current year
        cur = con.cursor()
        cur.execute(
            f"SELECT * FROM papers where papers.year {scope} order by citation_count desc limit 100"
        )
        rows = cur.fetchall()
        json_rows = [
            {"url": url, "title": title, "cites": cites}
            for url, year, title, cites in rows
        ]
        with open(f"_data/papers_{name}.json", "w") as f:
            json.dump(json_rows, f)
    con.commit()
