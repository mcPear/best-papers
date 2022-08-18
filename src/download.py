import requests
import xmltodict
import re
from tqdm import tqdm
from retry import retry
import traceback
from operator import itemgetter
import sqlite3
import asyncio
import aiohttp
from src.constants import *


def get_short_id(id):
    return "arxiv:" + re.search(r"[0-9]+\.[0-9]+", id)[0]


async def get(id, session):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{id}?fields=citationCount"
    try:
        async with session.get(url=url, headers={"x-api-key": api_key}) as response:
            response = response
            json_response = await response.json()
            return json_response["citationCount"]
    except Exception as e:
        print(e, "paper id: ", id)
        traceback.print_exc()


async def _request_cites_counts(ids):
    async with aiohttp.ClientSession() as session:
        cites_counts = await asyncio.gather(*[get(id, session) for id in ids])
        return cites_counts


def request_cites_counts(ids):
    return asyncio.run(_request_cites_counts(ids))


with open("api_key.txt") as f:
    api_key = f.readline()


def parse_arxiv_paper(e):
    result = {
        k: e.get(k)
        for k in [
            "id",
            "published",
            "title",
        ]
    }
    return result


@retry(tries=10, delay=1)
def request_arxiv(i, page_size):
    url = f"http://export.arxiv.org/api/query?search_query=all:cs.CL&start={i*page_size}&max_results={page_size}&sortBy=submittedDate&sortOrder=descending"
    r = requests.get(url).content
    entry = xmltodict.parse(r)["feed"].get("entry")
    if not entry:
        raise Exception(
            f"Error requesting papers from {i*page_size} to {(i+1)*page_size}", r
        )
    return entry


def escape_string(text):
    return text.replace("'", "''")


offset = 0
n_pages = 500
page_size = 100  # max SemanticSearch API per second


with sqlite3.connect(DATABASE_FILE_NAME) as con:
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS papers (id text PRIMARY KEY, published date, title text, citation_count int)"""
    )
    con.commit()

    for i in tqdm(range(offset, offset + n_pages)):
        arxiv_papers = request_arxiv(i, page_size)
        paper_ids = [get_short_id(e["id"]) for e in arxiv_papers]
        cites_counts = request_cites_counts(paper_ids)
        cur = con.cursor()
        insert_data = []
        for paper_dict, cites_count in tqdm(zip(arxiv_papers, cites_counts)):
            if cites_count is not None:
                id, published, title = itemgetter("id", "published", "title")(
                    paper_dict
                )
                title = escape_string(title)
                insert_data.append((id, published, title, cites_count))
        insert_sql = f"INSERT OR REPLACE INTO papers VALUES (?, ?, ?, ?)"
        cur.executemany(insert_sql, insert_data)
        con.commit()
