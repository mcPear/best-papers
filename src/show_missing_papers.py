import sqlite3
from src.constants import *

with sqlite3.connect(DATABASE_FILE_NAME) as con:
    cur = con.cursor()
    cur.execute(f"SELECT * FROM missing_papers")
    rows = cur.fetchall()
    print("Missing papers:")
    for row in rows:
        print(row)
