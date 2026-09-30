import os
from datetime import datetime, timezone

from flask import Flask, Response, abort, request, send_from_directory

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

# CROSS_DOMAIN_CANONICAL_v1 (2026-09-30): the ONE address every copy of this
# page claims as its own - canonical tag, share tags, structured data.
#
# It used to be northpointsg.com, and each host rewrote the address to name
# ITSELF. That made two websites serving byte-identical content, each
# self-canonicalising: textbook duplicate content. Google picks one and
# suppresses the other, and inbound links split between them.
#
# northpointsearchgroup.com wins because it matches the brand people search
# for, it is already what hundredx records as the firm's domain and what
# candidate reference forms print, and Search Console shows it with the
# larger share of traffic. northpointsg.com keeps serving the site and
# keeps its own Search Console property; it just points here.
CANONICAL = os.environ.get(
    "CANONICAL_URL", "https://www.northpointsearchgroup.com").rstrip("/")

# Still needed for robots.txt and sitemap.xml, which stay PER-HOST so each
# verified property advertises its own sitemap. Only the canonical is shared.
_SITE_HOSTS = {
    "northpointsg.com": "https://www.northpointsg.com",
    "www.northpointsg.com": "https://www.northpointsg.com",
    "northpointsearchgroup.com": "https://www.northpointsearchgroup.com",
    "www.northpointsearchgroup.com": "https://www.northpointsearchgroup.com",
}

# Only these kinds of files are served - never the site's own code or the git folder.
_PUBLIC_EXT = {".html", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
               ".css", ".js", ".pdf", ".woff", ".woff2", ".mp4"}


def _site_url() -> str:
    """The https address of the site the visitor asked for."""
    host = (request.host or "").split(":")[0].lower()
    return _SITE_HOSTS.get(host, CANONICAL)


def _serve_text(filename: str, mimetype: str) -> Response:
    """Serve a text file exactly as it is on disk.

    Deliberately NOT per-host. This used to swap the address for whichever
    host the visitor arrived on, which is what created the duplicate-content
    problem: both domains claimed themselves as canonical. Every visitor now
    gets the same CANONICAL address, so the two hosts consolidate into one
    result instead of competing.

    The files themselves are written with the canonical address, so there is
    nothing to substitute. Keep it that way - if you reintroduce a rewrite
    here, you reintroduce the duplicate content.
    """
    with open(os.path.join(BASE, filename), encoding="utf-8") as f:
        return Response(f.read(), mimetype=mimetype)


@app.route('/')
def index():
    return _serve_text('index.html', "text/html")


# Search engines and AI assistants are all welcome (listed by name so it's explicit).
_AI_CRAWLERS = ("Googlebot", "Bingbot", "GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot",
                "Claude-SearchBot", "Claude-User", "anthropic-ai", "PerplexityBot", "Perplexity-User",
                "Google-Extended", "Applebot", "Applebot-Extended", "CCBot", "meta-externalagent",
                "Amazonbot", "DuckAssistBot", "cohere-ai")


@app.route('/robots.txt')
def robots():
    lines = ["User-agent: *", "Allow: /", ""]
    for bot in _AI_CRAWLERS:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines.append(f"Sitemap: {_site_url()}/sitemap.xml")
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


@app.route('/llms.txt')
def llms_txt():
    """Plain-language summary for AI assistants (llmstxt.org convention)."""
    return _serve_text('llms.txt', "text/plain")


@app.route('/sitemap.xml')
def sitemap():
    """The site is one page, so the sitemap is one URL - and that is correct.

    Deliberately NOT listed:
      - the #section anchors. Google resolves a fragment to the page it sits
        on, so "/#services" is the same URL as "/". Listing them adds nothing
        and only pads the file.
      - the job board, which lives on host.pcrecruiter.net. A sitemap may only
        contain URLs on its own host.
      - /llms.txt and /robots.txt, which are not pages for search results.

    If this site is ever split into real pages (services, practice areas,
    about), list them here - that is the change that would actually give
    Search Console something to work with.
    """
    # index.html's mtime is the deploy time on Render, which is a fair answer
    # to "when did this page last change". Full W3C datetime rather than a
    # bare date so there is no ambiguity about the timezone.
    lastmod = datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, 'index.html')),
                                     tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f'  <url><loc>{_site_url()}/</loc><lastmod>{lastmod}</lastmod>'
           # the page now carries two live candidate feeds, so it genuinely
           # changes more often than the old "monthly" claimed.
           '<changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
           '</urlset>\n')
    return Response(xml, mimetype="application/xml")


@app.route('/<path:filename>')
def static_files(filename):
    parts = filename.replace('\\', '/').split('/')
    if any(p.startswith('.') for p in parts):
        abort(404)
    if os.path.splitext(filename)[1].lower() not in _PUBLIC_EXT:
        abort(404)
    return send_from_directory(BASE, filename)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
