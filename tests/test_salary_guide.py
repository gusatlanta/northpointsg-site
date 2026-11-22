"""The on-site salary guide keeps the visitor on NorthPoint and only adds a lead."""

import json
import re
import unittest

import app as site

ENDPOINT = "https://100xrecruiting.com/api/public/salary-guide"
HEADLINE = "Know what talent will accept"
SUBLINE = "Free 2026 salary guides. Download them right away."
THANKS = "Your guides are ready. Download them now."
BULLETS = (
    "See what people in your field are asking to be paid before you make an offer.",
    "Use one place for the desks NorthPoint hires in, from marketing and HR to the specialty brands in this family.",
    "Walk into a search with a range, not a guess.",
)
# Real 100X Workforce files. There is no Sales file and no NorthPoint-branded pack.
GUIDE_IDS = (
    "accounting-finance",
    "legal",
    "marketing",
    "hr-recruiting",
    "operations-admin",
    "engineering",
    "it",
    "recruiters",
    "military",
    "live-events",
    "virtual-assistants",
)


class SalaryGuideTest(unittest.TestCase):
    def setUp(self):
        self.client = site.app.test_client()

    def page(self, path):
        response = self.client.get(path)
        self.addCleanup(response.close)
        self.assertEqual(response.status_code, 200, path)
        return response.get_data(as_text=True)

    def test_offer_page_uses_marketing_copy_and_posts_a_new_lead(self):
        html = self.page("/salary-guide")
        self.assertIn(HEADLINE, html)
        self.assertIn(SUBLINE, html)
        self.assertIn(THANKS, html)
        for line in BULLETS:
            self.assertIn(line, html)
        self.assertIn(f'action="{ENDPOINT}"', html)
        self.assertIn("method=\"post\"", html.lower())
        self.assertIn(ENDPOINT, html)
        self.assertNotIn("api/public/inquiry", html)
        self.assertNotRegex(html, r"method:\s*['\"](?:PUT|PATCH|DELETE)['\"]")
        self.assertIn('name="brand" value="wf"', html)
        self.assertIn('name="website"', html)
        self.assertIn(">Name<", html)
        self.assertIn(">Email<", html)
        self.assertIn(">Company<", html)
        self.assertIn(">Role or job title<", html)
        self.assertIn(">Zip (optional)<", html)
        self.assertIn(">Get Started<", html)
        self.assertEqual(len(re.findall(r"<button\b[^>]*>\s*Get Started\s*</button>", html)), 1)
        self.assertNotRegex(html, r"<a\b[^>]*>\s*Get Started")
        self.assertIn("background: #17803d", self.page("/css/salary-guide.css"))
        for word in ("permanent", "PDL", "People Data Labs", "Claude", "Scout", "ZipApply", "MyZipApply"):
            self.assertNotIn(word, html)
        self.assertNotRegex(html, r"video r[eé]sum[eé]", re.I)
        self.assertNotRegex(html, r"\$\d")
        guides = json.loads(re.search(r'<script type="application/json" id="sg-guides">(.*?)</script>', html, re.S).group(1))
        self.assertEqual([g["id"] for g in guides], list(GUIDE_IDS))
        for guide in guides:
            self.assertTrue(guide["pdf"].startswith("https://100xworkforce.com/static/marketing/guides/"))
            self.assertTrue(guide["pdf"].endswith(".pdf"))
            self.assertIn(f'value="{guide["id"]}"', html)
        self.assertNotIn("sales", [g["id"] for g in guides])
        self.assertIn('href="https://www.northpointsearchgroup.com/salary-guide"', html)
        self.assertEqual(html.count(site.GA_MEASUREMENT_ID), 2)

    def test_pretty_path_and_file_path_both_serve_the_page(self):
        for path in ("/salary-guide", "/salary-guide/", "/salary-guide.html"):
            html = self.page(path)
            self.assertIn(HEADLINE, html)
            self.assertIn(site.GA_MEASUREMENT_ID, html)

    def test_home_band_stays_on_this_site(self):
        html = self.page("/")
        self.assertNotIn("100xworkforce.com/salary-guide", html)
        for guide_id in GUIDE_IDS[:7]:
            self.assertIn(f'href="/salary-guide#{guide_id}"', html)
        self.assertIn('href="/salary-guide">Salary Guides</a>', html)

    def test_sitemap_lists_the_pretty_url_once(self):
        xml = self.page("/sitemap.xml")
        self.assertEqual(xml.count("https://www.northpointsearchgroup.com/salary-guide"), 1)
        self.assertNotIn("/salary-guide.html", xml)


if __name__ == "__main__":
    unittest.main()
