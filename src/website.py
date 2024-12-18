import json
from src.database import create_connection, unescape_string
from src.scope import MIN_YEAR, MAX_YEAR
import yaml

INDEX_PAGE_ID = str(MAX_YEAR)

page_header_template = """---
layout: single
title: {title}
permalink: /nlp/papers/{id}/
---
"""

index_page_header_template = """---
layout: single
title: {title}
sidebar:
  nav: "scope_nav"
---
"""

page_content_template = """
<div>
<p class="featured_snippet">{featured_snippet}</p>
{% for paper in site.data.papers_{id} %}
    <h4>{{ paper.no }}. <a href="{{ paper.url }}" style="text-decoration:none" target="_blank">{{ paper.title }}</a></h4>

    <p class="cites"> {{ paper.cites }} citations</p>

    {% if paper.abstract != null %}
    <div class="abstract">
    <p>{{ paper.abstract }}</p>
    </div>
    {% endif %}
{% endfor %}
</div>

"""


def get_scopes():
    scopes = []
    for year in reversed(range(MIN_YEAR, MAX_YEAR + 1)):
        scopes.append(
            (f"= {year}", str(year), str(year), f"The best NLP papers of {year}")
        )
    scopes.append(
        (
            f"> {MAX_YEAR - 2}",
            "2",
            "The last 2 years",
            "The best NLP papers in the last 2 years",
        )
    )
    scopes.append(
        (
            f"> {MAX_YEAR - 5}",
            "5",
            "The last 5 years",
            "The best NLP papers in the last 5 years",
        )
    )
    scopes.append(
        (
            f">= {MIN_YEAR}",
            "all",
            f"From {MIN_YEAR}",
            f"The best NLP papers from {MIN_YEAR} to now",
        )
    )
    return scopes


def get_paper_url(id):
    return f"https://arxiv.org/abs/{id}"


def get_papers(connection, scope):
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT id, title, citation_count, abstract FROM papers where papers.year {scope} order by citation_count desc limit 100"
    )
    rows = cursor.fetchall()
    connection.commit()
    papers = [
        {
            "url": get_paper_url(id),
            "title": unescape_string(title),
            "cites": format_cites(cites),
            "abstract": unescape_string(abstract),
            "no": idx + 1,
        }
        for idx, (id, title, cites, abstract) in enumerate(rows)
    ]
    return papers


def format_cites(cites):
    return format(cites, ",").replace(",", " ") if cites else cites


def export_papers(papers, id):
    with open(f"_data/papers_{id}.json", "w") as f:
        json.dump(papers, f)


def build_page(id, title):
    with open(f"pages/{id}.md", "w") as f:
        page_header = page_header_template.replace("{title}", title).replace("{id}", id)
        page_content = page_content_template.replace("{id}", id).replace(
            "{featured_snippet}", get_featured_snippet(id)
        )
        page = page_header + page_content
        f.write(page)


def build_index_page(id, title):
    with open(f"index.markdown", "w") as f:
        page_header = index_page_header_template.replace("{title}", title)
        page_content = page_content_template.replace("{id}", id).replace(
            "{featured_snippet}", get_featured_snippet(id)
        )
        page = page_header + page_content
        f.write(page)


def get_featured_snippet(id):
    with open(f"featured_snippets/{id}.txt", "r") as f:
        return f.read()


def build_navigation(scopes):
    navigation = {
        "scope_nav": [
            {
                "title": "Select the scope",
                "children": [
                    {"title": name, "url": f"/nlp/papers/{id}/"}
                    for _scope, id, name, _title in scopes
                ],
            }
        ],
        "main": [{"title": "About", "url": "/about/"}],
    }
    with open("_data/navigation.yml", "w") as f:
        yaml.dump(
            navigation,
            f,
        )


def generate():
    with create_connection() as connection:
        scopes = get_scopes()
        for scope, id, _name, title in scopes:
            papers = get_papers(connection, scope)
            export_papers(papers, id)
            build_page(id, title)
            if id == INDEX_PAGE_ID:
                build_index_page(id, title)
        build_navigation(scopes)
