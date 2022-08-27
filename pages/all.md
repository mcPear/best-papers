---
layout: single
title: From 2013
permalink: /pages/all/
---

<span>Papers are ordered by citation counts.</span>

<ul>

{% for paper in site.data.papers_all %}

<li>
<a href="{{ paper.url }}">
{{ paper.title }}
</a> {{ paper.cites }}
</li>
{% endfor %}

</ul>
