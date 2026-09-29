import os
from datetime import datetime, timezone

from flask import Flask, Response, abort, send_from_directory

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

# The address Google should index (matches the canonical tag in index.html).
CANONICAL = os.environ.get("CANONICAL_URL", "https://www.northpointsg.com").rstrip("/")

# Only these kinds of files are served - never the site's own code or the git folder.
_PUBLIC_EXT = {".html", ".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg", ".ico",
               ".css", ".js", ".pdf", ".woff", ".woff2", ".mp4"}


@app.route('/')
def index():
    return send_from_directory(BASE, 'index.html')


@app.route('/robots.txt')
def robots():
    return Response(f"User-agent: *\nAllow: /\n\nSitemap: {CANONICAL}/sitemap.xml\n",
                    mimetype="text/plain")


@app.route('/sitemap.xml')
def sitemap():
    lastmod = datetime.fromtimestamp(os.path.getmtime(os.path.join(BASE, 'index.html')),
                                     tz=timezone.utc).strftime('%Y-%m-%d')
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
           f'  <url><loc>{CANONICAL}/</loc><lastmod>{lastmod}</lastmod>'
           '<changefreq>monthly</changefreq><priority>1.0</priority></url>\n'
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
