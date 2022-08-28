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
from os import environ


def get_short_id(id):
    return "arxiv:" + re.search(r"[0-9]+\.[0-9]+", id)[0]


async def get_ss(
    id, session, fields
):  # TODO handle exceeding request rate limit explicitly
    api_key = environ["SS_API_KEY"]
    fields_csv = ",".join(fields)
    arxiv_id_url = (
        f"https://api.semanticscholar.org/graph/v1/paper/{id}?fields={fields_csv}"
    )
    # FIXME search for the paper by title if arxiv id doesn't work
    # https://www.semanticscholar.org/product/api
    search_url = "https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_name}h&limit=1"
    # https://api.semanticscholar.org/graph/v1/paper/search?query=SGPT%3A%20GPT%20Sentence%20Embeddings%20for%20Semantic%20Search&limit=1
    ss_id_url = "https://api.semanticscholar.org/graph/v1/paper/{ss_id}?fields=title"
    # https://api.semanticscholar.org/graph/v1/paper/cf8235e0b592f52848c3dc4a9b76222c25d172cb?fields=title,embedding
    try:
        async with session.get(
            url=arxiv_id_url, headers={"x-api-key": api_key}
        ) as response:
            json_response = await response.json()
            if any([field not in json_response for field in fields]):
                print(response)
            return {field: json_response[field] for field in fields}
    except Exception as e:
        print(e, "paper id: ", id)
        traceback.print_exc()


async def _request_ss(ids, fields):
    async with aiohttp.ClientSession() as session:
        cites_counts = await asyncio.gather(
            *[get_ss(id, session, fields) for id in ids]
        )
        return cites_counts


def request_ss(ids, fields):
    return asyncio.run(_request_ss(ids, fields))


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


@retry(tries=10, delay=4)
def request_arxiv(i, page_size):
    url = f"http://export.arxiv.org/api/query?search_query=all:cs.CL&start={i*page_size}&max_results={page_size}&sortBy=submittedDate&sortOrder=descending"
    r = requests.get(url).content
    entry = xmltodict.parse(r)["feed"].get("entry")
    if not entry:
        print("Missing entry in request", str(r))
        raise Exception(
            f"Error requesting papers from {i*page_size} to {(i+1)*page_size}", r
        )
    return entry


def escape_string(text):
    return text.replace("'", "''")


offset = 0
n_pages = 500 - offset
page_size = 100  # max SemanticScholar API requests per second


with sqlite3.connect(DATABASE_FILE_NAME) as con:
    cur = con.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS papers (id text PRIMARY KEY, year int, title text, citation_count int)"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS missing_papers (id text PRIMARY KEY, title text)"""
    )
    con.commit()

    for i in tqdm(range(offset, offset + n_pages)):
        arxiv_papers = request_arxiv(i, page_size)
        paper_ids = [get_short_id(e["id"]) for e in arxiv_papers]
        paper_titles = [e["title"] for e in arxiv_papers]
        arxiv_fields = ["id", "title"]
        ss_fields = [
            "citationCount",
            "year",
        ]  # We take year from SS since arXiv's published_at is sometimes not related to creation date
        ss_papers = request_ss(paper_ids, ss_fields)
        cur = con.cursor()
        insert_data = []
        insert_missing_data = []
        for arxiv_paper_dict, ss_paper_dict in tqdm(zip(arxiv_papers, ss_papers)):
            id, title = itemgetter(*arxiv_fields)(arxiv_paper_dict)
            title = escape_string(title)
            if ss_paper_dict is not None:
                cites_count, year = itemgetter(*ss_fields)(ss_paper_dict)
                insert_data.append((id, year, title, cites_count))
            else:
                insert_missing_data.append((id, title))
        insert_sql = f"INSERT OR REPLACE INTO papers VALUES (?, ?, ?, ?)"
        cur.executemany(insert_sql, insert_data)
        insert_missing_sql = f"INSERT OR REPLACE INTO missing_papers VALUES (?, ?)"
        cur.executemany(insert_missing_sql, insert_missing_data)
        con.commit()

    cur.execute(f"SELECT * FROM missing_papers")
    rows = cur.fetchall()
    print("Missing papers:")
    for row in rows:
        print(row)
