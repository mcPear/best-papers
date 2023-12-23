---
layout: single
title: The best NLP papers of 2023
sidebar:
  nav: "scope_nav"
---

<div>
{% for paper in site.data.papers_2023 %}
    <h4>{{ paper.no }}. <a href="{{ paper.url }}" style="text-decoration:none">{{ paper.title }}</a></h4>

    <p class="cites"> {{ paper.cites }} citations</p>

    {% if paper.abstract != null %}
    <div class="abstract">
    <p>{{ paper.abstract }}</p>
    </div>
    {% endif %}
{% endfor %}
</div>

