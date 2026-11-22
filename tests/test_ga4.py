"""The GA4 tag is injected into every HTML page the site serves."""

import os
import unittest

import app as site

# The pages a visitor actually lands on. City pages are covered by the
# walk of every .html file below; these are named so a failure says which
# main page lost the tag.
_MAIN_PAGES = (
    "/",
    "/marketing-recruiters.html",
    "/sales-recruiters.html",
    "/hr-recruiters.html",
    "/executive-search/",
    "/salary-guide",
)


def _html_paths():
    paths = ["/"]
    for root, dirs, files in os.walk(site.BASE):
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".") and d not in ("__pycache__", "venv", ".venv", "tests")
        )
        for name in sorted(files):
            if not name.endswith(".html"):
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, site.BASE).replace(os.sep, "/")
            if rel == "index.html":
                continue
            loc = rel[: -len("index.html")] if name == "index.html" else rel
            paths.append("/" + loc)
    return paths


class Ga4TagTest(unittest.TestCase):
    def setUp(self):
        self.client = site.app.test_client()

    def assertTagInHead(self, path, headers=None):
        response = self.client.get(path, headers=headers)
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200, path)
        self.assertEqual(response.mimetype, "text/html", path)
        html = response.get_data(as_text=True)
        head_end = html.lower().find("</head>")
        head_start = html.lower().find("<head")
        self.assertGreater(head_start, -1, path)
        self.assertGreater(head_end, head_start, path)
        head = html[head_start:head_end]
        self.assertIn(site.GA_MEASUREMENT_ID, head, path)
        self.assertIn(
            f"https://www.googletagmanager.com/gtag/js?id={site.GA_MEASUREMENT_ID}",
            head,
            path,
        )
        self.assertIn(f"gtag('config', '{site.GA_MEASUREMENT_ID}')", head, path)
        self.assertEqual(html.count(site.GA_MEASUREMENT_ID), 2, path)
        return response

    def test_tag_is_on_the_main_pages(self):
        for path in _MAIN_PAGES:
            with self.subTest(path=path):
                self.assertTagInHead(path)

    def test_tag_is_on_every_html_page(self):
        pages = _html_paths()
        self.assertGreaterEqual(len(pages), len(_MAIN_PAGES))
        for path in pages:
            with self.subTest(path=path):
                self.assertTagInHead(path)

    def test_revalidation_still_returns_the_tag(self):
        """A browser rechecking a cached page still gets the tag.

        HTML used to 304 from the file on disk. That response has no body,
        so the tag would never show up for a visitor who already had the page.
        """
        first = self.assertTagInHead("/marketing-recruiters.html")
        self.assertTagInHead(
            "/marketing-recruiters.html",
            headers={
                "If-None-Match": first.headers["ETag"],
                "If-Modified-Since": first.headers["Last-Modified"],
            },
        )
        self.assertTagInHead(
            "/",
            headers={"If-Modified-Since": "Tue, 01 Jan 2030 00:00:00 GMT"},
        )

    def test_tag_is_not_on_non_html(self):
        for path in ("/robots.txt", "/llms.txt", "/sitemap.xml", "/css/np.css"):
            response = self.client.get(path)
            self.addCleanup(response.close)
            self.assertEqual(response.status_code, 200, path)
            self.assertNotIn(site.GA_MEASUREMENT_ID, response.get_data(as_text=True), path)


if __name__ == "__main__":
    unittest.main()
