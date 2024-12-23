---
layout: single
title: The best NLP papers of 2024
sidebar:
  nav: "scope_nav"
---

<div>
<p class="featured_snippet">The best NLP papers of 2024 cover a range of groundbreaking advancements, including the development of new language models like Mixtral 8x7B and Gemini 1.5, innovations in multimodal understanding, open-source code intelligence with DeepSeek-Coder, and comprehensive reviews on counterfactual generation in NLP. These papers push the boundaries of language model capabilities, efficiency, and application across diverse tasks and domains.</p>
{% for paper in site.data.papers_2024 %}
    <h4>{{ paper.no }}. <a href="{{ paper.url }}" style="text-decoration:none" target="_blank">{{ paper.title }}</a></h4>

    <p class="cites"> {{ paper.cites }} citations</p>

    {% if paper.abstract != null %}
    <div class="abstract">
    <p>{{ paper.abstract }}</p>
    </div>
    {% endif %}
{% endfor %}
</div>

