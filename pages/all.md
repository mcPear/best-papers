---
layout: single
title: The best NLP papers from 2013 to now
permalink: /nlp/papers/all/
---

<div>
{% for paper in site.data.papers_all %}
    <h4>{{ paper.no }}. <a href="{{ paper.url }}" style="text-decoration:none">{{ paper.title }}</a></h4>

    <p style="font-size: 0.8em; font-weight: bold;"> {{ paper.cites }} citations</p>

    {% if paper.abstract != null %}
    <div style="width: 100%; height: 200px; overflow-y: scroll">
    <p style="font-size: 0.8em">{{ paper.abstract }}</p>
    </div>
    {% endif %}
{% endfor %}
</div>

