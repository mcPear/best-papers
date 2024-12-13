import traceback
from urllib import request, parse, error
import json
from os import environ
import logging
from src.database import (
    select_papers_missing_citations_count,
    update_citation_count,
    update_semantic_scholar_id,
    select_papers_with_semantic_scholar_id,
)
from tqdm import tqdm
from time import time, sleep
import urllib
from retry import retry

API_KEY = environ["SS_API_KEY"]
API_URL = "https://api.semanticscholar.org/graph/v1"
BATCH_SIZE = 500
DELAY_TIME = 1

# TODO introduce last_update_date to handle interruptions and reruns


@retry(tries=5, delay=DELAY_TIME, max_delay=2 * DELAY_TIME)
def make_request(url, method="GET", data=None):
    headers = {"x-api-key": API_KEY}
    if data:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode("utf-8")

    req = request.Request(url, data=data, headers=headers, method=method)
    with request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_papers_by_ids(papers):
    # Use semantic scholar IDs directly if available, otherwise use arxiv format
    ids = [
        paper.get("semantic_scholar_id") or f"arxiv:{paper['id']}" for paper in papers
    ]

    try:
        url = f"{API_URL}/paper/batch?fields=citationCount"
        results = make_request(url, method="POST", data={"ids": ids})
    except error.HTTPError as e:
        raise Exception(f"Failed batch request with status {e.code}")

    found_papers = []
    for paper, result in zip(papers, results):
        if result:
            found_papers.append(
                {"id": paper["id"], "citationCount": result["citationCount"]}
            )
        else:
            logging.info(
                f'Paper "{paper["title"]}" (id: {paper["id"]}) not found by ID in Semantic Scholar.'
            )

    return found_papers


def fetch_paper_id_by_title(id, title):
    try:
        url = f"{API_URL}/paper/search/match?query={parse.quote(title)}&fields=paperId"
        data = make_request(url)
    except error.HTTPError as e:
        if e.code == 404:
            logging.info(
                f'Paper {id} "{title}" not found by title in Semantic Scholar.'
            )
            return None
        raise e

    matches = data["data"]
    if matches == []:
        logging.info(f'Paper {id} "{title}" not found by title in Semantic Scholar.')
        return None
    else:
        return {"id": id, "semantic_scholar_id": matches[0]["paperId"]}


def fetch_missing_papers_by_titles(papers):
    results = []
    last_fetch_time = 0

    for paper in tqdm(papers):
        try:
            delay(last_fetch_time)
            result = fetch_paper_by_title(paper["id"], paper["title"])
            last_fetch_time = time()
            if result:
                results.append(result)
        except Exception as e:
            logging.error(f"Error searching paper by title: {paper['id']}, {str(e)}")
    return results


def get_batches(l):
    return tqdm([l[i : i + BATCH_SIZE] for i in range(0, len(l), BATCH_SIZE)])


def store_papers(papers):
    update_citation_count(papers)
    logging.info(f"Stored {len(papers)} papers.")


def delay(last_fetch_time):
    time_from_last_fetch = time() - last_fetch_time
    sleep_time = max(0, DELAY_TIME - time_from_last_fetch)
    sleep(sleep_time)


def get_batched_papers():
    papers = select_papers_missing_citations_count()
    batches = get_batches(papers)
    return batches, len(papers)


def fetch_citation_counts_by_arxiv_id():
    last_fetch_time = 0
    batched_papers, papers_count = get_batched_papers()

    logging.info(f"Fetching {papers_count} papers by arxiv ID...")
    for batch in batched_papers:
        delay(last_fetch_time)
        found_papers = fetch_papers_by_ids(batch)
        last_fetch_time = time()
        store_papers(found_papers)


def fetch_semantic_scholar_ids_by_titles():
    last_fetch_time = 0
    papers = select_papers_missing_citations_count()
    if not papers:
        logging.info("No papers need semantic scholar ID lookup.")
        return

    logging.info(f"Fetching semantic scholar IDs for {len(papers)} papers by title...")
    results = []
    delay(DELAY_TIME)
    for paper in tqdm(papers):
        delay(last_fetch_time)
        result = fetch_paper_id_by_title(paper["id"], paper["title"])
        last_fetch_time = time()
        if result:
            results.append(result)
    update_semantic_scholar_id(results)


def fetch_citation_counts_by_semantic_ids():
    last_fetch_time = 0
    papers = select_papers_with_semantic_scholar_id()
    if not papers:
        logging.info("No papers need citation count updates.")
        return

    logging.info(
        f"Fetching citation counts for {len(papers)} papers using Semantic Scholar IDs..."
    )
    delay(DELAY_TIME)
    for batch in get_batches(papers):
        delay(last_fetch_time)
        found_papers = fetch_papers_by_ids(batch)
        last_fetch_time = time()
        store_papers(found_papers)


def download():
    fetch_citation_counts_by_arxiv_id()
    fetch_semantic_scholar_ids_by_titles()
    fetch_citation_counts_by_semantic_ids()
    logging.info("Finished fetching citation counts from Semantic Scholar.")
