---
layout: single
title: From 2013
permalink: /pages/all/
---

<ul>
<!-- TODO generate pages and navigation https://jekyllrb.com/docs/plugins/generators/ or hardcode everything to deploy faster - better -->
    {% for paper in site.data.papers_all %}
      <li>
        <a href="{{ paper.url }}">
            {{ paper.title }}
        </a> {{ paper.cites }}
      </li>
    {% endfor %}
</ul>
