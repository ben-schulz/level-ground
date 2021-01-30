import re
import requests
import asyncio
import os
import datetime

import urllib
from html.parser import HTMLParser
from html.entities import name2codepoint

from extracts import PublicUrl
from extracts.converters import excel_to_csv

_today = datetime.datetime.utcnow()
formatstr = "%Y-%m-%d"
utc_datestamp = _today.strftime(formatstr)
cst_datestamp = (_today - datetime.timedelta(days=1)).strftime(formatstr)

file_dump_path = os.path.expanduser("~/extract_dump")

frontpage_url = "https://www.boonecountymo.org/sheriff/jail/operations.asp"
base_report_url = "https://report.boonecountymo.org/mrcjava/servlet/"


def report_url(relative):
    return urllib.parse.urljoin(base_report_url, relative)


class UrlScraper(HTMLParser):
    def _get_href_attr(attrs):
        href = [value for (key, value) in attrs if key == "href"]
        if href:
            return href[0]

    def __init__(self, target_string, *args, **kwargs):
        self.target_string = target_string
        self.current_anchor = None
        self.target = None
        HTMLParser.__init__(self, *args, **kwargs)

    def handle_starttag(self, tag, attrs):
        if "a" == tag:
            href = UrlScraper._get_href_attr(attrs)
            self.current_anchor = href

    def handle_data(self, data):
        if self.target_string in data:
            self.target = self.current_anchor


def get_report_page_urls():
    frontpage = requests.get(frontpage_url)
    front_text = frontpage.text

    sevenhundred_parser = UrlScraper("07:00 Report")
    sevenhundred_parser.feed(front_text)
    currentdetainees_parser = UrlScraper("Current Detainees")
    currentdetainees_parser.feed(front_text)

    return (
        sevenhundred_parser.target,
        currentdetainees_parser.target,
    )


def get_sevenhundred_download(target_url):
    return PublicUrl(
        "0700-report-page",
        target_url,
        file_dump_path,
        headers={
            "Host": "report.boonecountymo.org",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
        },
    )


def get_currentdetainees_download(target_url):
    return PublicUrl(
        "current-detainees-page",
        target_url,
        file_dump_path,
        headers={
            "Host": "report.boonecountymo.org",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:78.0) Gecko/20100101 Firefox/78.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
        },
    )


async def _run_fetches(sources):
    await asyncio.gather(*(p.fetch() for p in sources))


def fetch_frontpages():

    sevenhundred_url, currentdetainees_url = get_report_page_urls()
    sevenhundred_frontpage = get_sevenhundred_download(sevenhundred_url)
    currentdetainees_frontpage = get_currentdetainees_download(currentdetainees_url)

    pages = [
        sevenhundred_frontpage,
        currentdetainees_frontpage,
    ]

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run_fetches(pages))

    sevenhundred_page_path = os.path.join(
        sevenhundred_frontpage.output_dir,
        sevenhundred_frontpage.datestamp_filename_today(),
    )
    currentdetainees_page_path = os.path.join(
        currentdetainees_frontpage.output_dir,
        currentdetainees_frontpage.datestamp_filename_today(),
    )

    return (sevenhundred_page_path, currentdetainees_page_path)


sevenhundred_page_path, currentdetainees_page_path = fetch_frontpages()


def download_sevenhundred_report():

    with open(sevenhundred_page_path, "r") as f:
        text = f.read()

    parser = UrlScraper("Export to Excel")
    result = parser.feed(text)

    return PublicUrl(
        "0700_report",
        report_url(parser.target),
        file_dump_path,
        output_converter=excel_to_csv,
        datestamp=cst_datestamp,
        file_suffix="xlsx",
        headers={
            "Host": "report.boonecountymo.org",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:79.0) Gecko/20100101 Firefox/79.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    )


def download_currentdetainees_report():

    with open(currentdetainees_page_path, "r") as f:
        text = f.read()

    parser = UrlScraper("Export Detainees & Charges to Excel")
    result = parser.feed(text)

    return PublicUrl(
        "current_detainees",
        report_url(parser.target),
        file_dump_path,
        output_converter=excel_to_csv,
        datestamp=cst_datestamp,
        file_suffix="xlsx",
        headers={
            "Host": "report.boonecountymo.org",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv: 79.0) Gecko/20100101 Firefox/79.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    )


downloads = [download_sevenhundred_report(), download_currentdetainees_report()]
loop = asyncio.get_event_loop()
loop.run_until_complete(_run_fetches(downloads))
