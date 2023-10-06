import traceback
import asyncio
import aiohttp
from os import environ
import logging
from src.database import select_papers, update_citation_count
from tqdm import tqdm
from time import time, sleep
import urllib

API_KEY = environ["SS_API_KEY"]

# 100 requests per second is API limit (but in worst case scenario we make 3 calls per paper)
BATCH_SIZE = 33
DELAY_TIME = 1


async def fetch_paper_by_semantic_scholar_id(id, semantic_scholar_id, session):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{semantic_scholar_id}?fields=citationCount"
    response = None
    async with session.get(url=url, headers={"x-api-key": API_KEY}) as response:
        status = response.status
        response = await response.json()
        if status == 404:
            logging.info(
                f"Paper {id} not found by Semantic Scholar id {semantic_scholar_id}."
            )
            return {"id": id, "citationCount": None}
        if "citationCount" in response:
            return {"id": id, "citationCount": response["citationCount"]}
        raise Exception(
            f"Unexpected response from Semantic Scholar:\n{response}\nURL: {url}"
        )


async def fetch_paper_by_title(id, title, session):
    encoded_title = urllib.parse.quote(title)
    url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_title}&limit=1"
    response = None
    async with session.get(url=url, headers={"x-api-key": API_KEY}) as response:
        status = response.status
        response = await response.json()
        if status == 404 or "total" in response and response["total"] == 0:
            logging.info(
                f'Paper {id} "{title}" not found by title in Semantic Scholar.'
            )
            return {"id": id, "citationCount": None}
        if "total" in response:
            semantic_scholar_id = response["data"][0]["paperId"]
            return await fetch_paper_by_semantic_scholar_id(
                id, semantic_scholar_id, session
            )
        raise Exception(
            f"Unexpected response from Semantic Scholar:\n{response}\nURL: {url}"
        )


async def fetch_paper_by_id(id, session):
    url = f"https://api.semanticscholar.org/graph/v1/paper/{'arxiv:' + id}?fields=citationCount"
    response = None
    async with session.get(url=url, headers={"x-api-key": API_KEY}) as response:
        status = response.status
        response = await response.json()
        if status == 404:
            logging.info(f"Paper {id} not found by id in Semantic Scholar.")
            return {"id": id, "citationCount": None}
        if "citationCount" in response:
            return {"id": id, "citationCount": response["citationCount"]}
        raise Exception(
            f"Unexpected response from Semantic Scholar:\n{response}\nURL: {url}"
        )


async def fetch_paper(paper, session):
    id = paper["id"]
    title = paper["title"]

    try:
        paper = await fetch_paper_by_id(id, session)
        if paper["citationCount"] is None:
            return await fetch_paper_by_title(id, title, session)
        return paper

    except Exception as e:
        error_message = f"Error fetching paper from Semantic Scholar.\nId: {id}\n Message:\n{e}\nResponse:\nTraceback:\n{traceback.format_exc()}"
        logging.error(error_message)


async def _fetch_papers(papers):
    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*[fetch_paper(paper, session) for paper in papers])


def fetch_papers(papers):
    return asyncio.run(_fetch_papers(papers))


def get_batches(l):
    return [l[i : i + BATCH_SIZE] for i in range(0, len(l), BATCH_SIZE)]


def store_papers(papers):
    update_citation_count(papers)
    logging.info(f"Stored {len(papers)} papers.")


def delay(last_fetch_time):
    time_from_last_fetch = time() - last_fetch_time
    sleep_time = max(0, DELAY_TIME - time_from_last_fetch)
    sleep(sleep_time)


def get_batched_papers():
    papers = select_papers()
    batches = get_batches(papers)
    return tqdm(batches)


def download():
    last_fetch_time = 0
    batched_papers = get_batched_papers()
    for batch in batched_papers:
        delay(last_fetch_time)
        papers = fetch_papers(batch)
        last_fetch_time = time()
        store_papers(papers)
