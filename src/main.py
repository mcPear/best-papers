import argparse
from dotenv import load_dotenv

load_dotenv()
from src import arxiv
from src import semantic_scholar
from src import website


parser = argparse.ArgumentParser()
parser.add_argument("-a", "--arxiv", action="store_true")
parser.add_argument("-s", "--semanticscholar", action="store_true")
parser.add_argument("-w", "--website", action="store_true")
args = parser.parse_args()

if args.arxiv:
    arxiv.download()
if args.semanticscholar:
    semantic_scholar.download()
if args.website:
    website.generate()
