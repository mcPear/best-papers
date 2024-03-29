---
layout: single
title: The best NLP papers of 2023
sidebar:
  nav: "scope_nav"
---

<div>
<p class="featured_snippet">The best NLP papers of 2023 cover a range of topics including the development of new language models like LLaMA and GPT-4, advancements in multimodal deep learning, the exploration of large language models' capabilities in problem-solving and reasoning, and the evaluation of these models across various tasks and domains.</p>
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

