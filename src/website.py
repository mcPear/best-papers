import json
from src.database import create_connection, unescape_string
from src.scope import MIN_YEAR, CURRENT_YEAR
import yaml

page_template = """---
layout: single
title: {title}
permalink: /pages/{name}/
---

<span>Papers are ordered by citation count.</span>

<ul>
    {% for paper in site.data.papers_{name} %}
      <li>
        <a href="{{ paper.url }}">
            {{ paper.title }}
        </a> {{ paper.cites }}
      </li>
    {% endfor %}
</ul>

"""


def get_scopes():
    scopes = []
    for year in reversed(range(MIN_YEAR, CURRENT_YEAR + 1)):
        scopes.append((f"= {year}", str(year), str(year)))
    scopes.append((f"> {CURRENT_YEAR - 2}", "2", "The last 2 years"))
    scopes.append((f"> {CURRENT_YEAR - 5}", "5", "The last 5 years"))
    scopes.append((f">= {MIN_YEAR}", "all", f"From {MIN_YEAR}"))
    return scopes


def get_paper_url(id):
    return f"https://arxiv.org/abs/{id}"


def get_papers(connection, scope):
    cursor = connection.cursor()
    cursor.execute(
        f"SELECT * FROM papers where papers.year {scope} order by citation_count desc limit 100"
    )
    rows = cursor.fetchall()
    connection.commit()
    papers = [
        {
            "url": get_paper_url(id),
            "title": unescape_string(title),
            "cites": cites,
        }
        for id, year, title, cites in rows
    ]
    return papers


def export_papers(papers, name):
    with open(f"_data/papers_{name}.json", "w") as f:
        json.dump(papers, f)


def build_page(name, title):
    with open(f"pages/{name}.md", "w") as f:
        f.write(page_template.replace("{title}", title).replace("{name}", name))


def build_navigation(scopes):
    navigation = {
        "scope_nav": [
            {
                "title": "Scope",
                "children": [
                    {"title": title, "url": f"/pages/{name}/"}
                    for scope, name, title in scopes
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
        for scope, name, title in scopes:
            papers = get_papers(connection, scope)
            export_papers(papers, name)
            build_page(name, title)
        build_navigation(scopes)
