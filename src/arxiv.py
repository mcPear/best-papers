import requests
import xmltodict
from retry import retry
from src.logging_config import logging
from datetime import datetime
from src.database import insert_or_replace, create_table
from time import time, sleep
from src.scope import MIN_YEAR

DEFAULT_FILTERS = {"min_year": MIN_YEAR, "category": "cs.CL"}

START_URL = (
    "https://export.arxiv.org/oai2?verb=ListRecords&set=cs&metadataPrefix=arXivRaw"
)
RESUMPTION_URL = "https://export.arxiv.org/oai2?verb=ListRecords&resumptionToken={}"
DELAY_TIME = 5


class RetryAfter5SecondsException(Exception):
    pass


def get_resumption_url(resumption_token):
    return RESUMPTION_URL.format(resumption_token)


def get_year(metadata):
    version = metadata["version"]
    date_str = version[0]["date"] if isinstance(version, list) else version["date"]
    date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
    return date.year


def parse_record(record):
    metadata = record["metadata"]["arXivRaw"]
    id = metadata["id"]
    title = metadata["title"]
    categories = metadata["categories"].split(" ")
    year = get_year(metadata)
    abstract = metadata["abstract"]
    return {
        "id": id,
        "title": title,
        "categories": categories,
        "year": year,
        "abstract": abstract,
    }


def request_page(url):
    response = requests.get(url)
    return xmltodict.parse(response.content)


def get_list_records(content):
    return content["OAI-PMH"]["ListRecords"]


def get_records(content):
    list_records = get_list_records(content)
    return list_records["record"]


def parse_records(records):
    return [parse_record(record) for record in records]


def filter_records(records, filters):
    return [
        record
        for record in records
        if record["year"] >= filters["min_year"]
        and filters["category"] in record["categories"]
    ]


def get_filtered_records(content, filters):
    records = get_records(content)
    records = parse_records(records)
    records = filter_records(records, filters)
    return records


def get_resumption_token(content):
    list_records = get_list_records(content)
    return list_records["resumptionToken"]


def log_progress(content):
    resumption_token = get_resumption_token(content)
    page_size = len(get_records(content))
    cursor = int(resumption_token["@cursor"])
    complete_list_size = int(resumption_token["@completeListSize"])
    current_records_count = cursor + page_size
    progress_percent = current_records_count / complete_list_size * 100
    logging.info(
        f"Progress: {current_records_count}/{complete_list_size} {progress_percent:.1f}%"
    )


def get_resumption_token_text(content):
    resumption_token = get_resumption_token(content)
    resumption_token_text = resumption_token.get("#text")
    logging.info(f"Resumption token: {resumption_token_text}")
    return resumption_token_text


def get_url(resumption_token):
    if resumption_token:
        return get_resumption_url(resumption_token)
    else:
        return START_URL


def handle_wait_request(content):
    if content == {"html": {"body": {"h1": "Retry after 5 seconds"}}}:
        raise RetryAfter5SecondsException()


@retry(
    exceptions=RetryAfter5SecondsException,
    tries=10,
    delay=5,
    jitter=(1, 3),
)
def fetch_page(filters, resumption_token=None):
    url = get_url(resumption_token)
    content = request_page(url)
    handle_wait_request(content)
    records = get_filtered_records(content, filters)
    log_progress(content)
    resumption_token = get_resumption_token_text(content)

    return (records, resumption_token)


def store_page(page):
    insert_or_replace(page)
    logging.info(f"Stored {len(page)} papers.")


def delay(last_fetch_time):
    time_from_last_fetch = time() - last_fetch_time
    sleep_time = max(0, DELAY_TIME - time_from_last_fetch)
    sleep(sleep_time)


def download(filters=DEFAULT_FILTERS):
    create_table()

    resumption_token = None
    last_fetch_time = 0
    while True:
        delay(last_fetch_time)
        (page, resumption_token) = fetch_page(filters, resumption_token)
        last_fetch_time = time()
        store_page(page)
        if not resumption_token:
            break
