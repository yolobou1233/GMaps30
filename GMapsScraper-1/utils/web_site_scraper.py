from selenium.webdriver.chrome.webdriver import WebDriver
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from re import compile

class PatternScraper:
    def __init__(self):
        self._last_opened_handler = None
        self._email_pattern = compile(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)*')
        self._fb_pattern = compile(r'(?:https?://)?(?:www\.)?facebook\.com/\S+')
        self._twitter_pattern = compile(r'(?:https?://)?(?:www\.)?twitter\.com/\S+')
        self._insta_pattern = compile(r'(?:https?://)?(?:www\.)?instagram\.com/\S+')
        self._youtube_pattern = compile(r'(?:https?://)?(?:www\.)?youtube\.com/\S+')
        self._linkedin_pattern = compile(r'(?:https?://)?(?:www\.)?linkedin\.com/\S+')

    @staticmethod
    def create_urls(site_url: str, url_ext: list):
        site_parser = urlparse(site_url)
        base_url = site_parser.netloc
        scheme = site_parser.scheme or "http"
        created_urls = []

        for url in url_ext:
            if site_url.endswith("/"):
                org_url = site_url + url
            else:
                created_urls.append(site_url + url)
                org_url = scheme + "://" + base_url + "/" + url

            created_urls.append(org_url)
        return created_urls

    def get_source_code(self, driver: WebDriver, urls: list):
        source_codes = []
        for url in urls:
            driver.execute_script(f'''window.open("{url}", "_blank");''')
            driver.switch_to.window(driver.window_handles[-1])
            source_codes.append(driver.page_source)
            driver.close()
            driver.switch_to.window(self._last_opened_handler)
        return source_codes

    @staticmethod
    def email_decoder(email):
        decoded_mail = ""
        k = int(email[:2], 16)
        for i in range(2, len(email) - 1, 2):
            decoded_mail += chr(int(email[i:i + 2], 16) ^ k)
        return decoded_mail

    def _href_emails(self, soup: BeautifulSoup) -> list:
        email_list = []
        mail_tos = soup.select('a[href]')
        for mail in mail_tos:
            href = mail['href']
            if "email-protect" in href:
                email_list.append(self.email_decoder(href.split("#")[1]))
            elif "mailto" in href:
                email_list.append(href.removeprefix("mailto:").strip())
        return email_list

    def get_pattern_data(self, source_codes: list):
        patterns_data = {"site_email": [], "facebook_links": [], "twitter_links": [], "instagram_links": [],
                         "youtube_links": [], "linkedin_links": []}

        for source in source_codes:
            soup = BeautifulSoup(source, features="lxml", parser="html.parser")

            site_email = [x for x in str(soup) if self._email_pattern.search(x).group()]
            if not site_email:
                href_emails = self._href_emails(soup)
                site_email.extend(href_emails)

            facebook_links = [link['href'] for link in soup.find_all('a', href=self._fb_pattern)]
            twitter_links = [link['href'] for link in soup.find_all('a', href=self._twitter_pattern)]
            instagram_links = [link['href'] for link in soup.find_all('a', href=self._insta_pattern)]
            youtube_links = [link['href'] for link in soup.find_all('a', href=self._youtube_pattern)]
            linkedin_links = [link['href'] for link in soup.find_all('a', href=self._linkedin_pattern)]

            patterns_data["site_email"].extend(site_email)
            patterns_data["facebook_links"].extend(facebook_links)
            patterns_data["twitter_links"].extend(twitter_links)
            patterns_data["instagram_links"].extend(instagram_links)
            patterns_data["youtube_links"].extend(youtube_links)
            patterns_data["linkedin_links"].extend(linkedin_links)
        return patterns_data

    def find_patterns(self, driver: WebDriver, site_url: str, suggested_ext: list, unavailable: str = "Not Available"):
        patterns_data = {"site_email": "", "facebook_links": "", "twitter_links": "", "instagram_links": "",
                         "youtube_links": "", "linkedin_links": ""}

        if site_url == unavailable or not suggested_ext:
            return {key: unavailable for key in patterns_data}

        valid_urls = self.create_urls(site_url, suggested_ext)

        self._last_opened_handler = driver.current_window_handle
        try:
            sources = self.get_source_code(driver, valid_urls)
        except Exception:
            return {key: unavailable for key in patterns_data}

        social_data = self.get_pattern_data(sources)

        return {key: (social_data[key][0] if social_data[key] else unavailable) for key in patterns_data}
