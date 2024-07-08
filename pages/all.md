---
layout: single
title: The best NLP papers from 2014 to now
permalink: /nlp/papers/all/
---

<div>
<p class="featured_snippet">The best NLP papers include "Attention Is All You Need", "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding", "Distributed Representations of Words and Phrases and their Compositionality", "Efficient Estimation of Word Representations in Vector Space", and "Neural Machine Translation by Jointly Learning to Align and Translate". These papers have made significant contributions to the field of NLP.</p>
{% for paper in site.data.papers_all %}
    <h4>{{ paper.no }}. <a href="{{ paper.url }}" style="text-decoration:none">{{ paper.title }}</a></h4>

    <p class="cites"> {{ paper.cites }} citations</p>

    {% if paper.abstract != null %}
    <div class="abstract">
    <p>{{ paper.abstract }}</p>
    </div>
    {% endif %}
{% endfor %}
</div>

