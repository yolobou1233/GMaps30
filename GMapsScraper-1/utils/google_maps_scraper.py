from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException, NoSuchElementException,
                                        StaleElementReferenceException, NoSuchWindowException)
from selenium_stealth import stealth
from os.path import exists
from os import mkdir
from time import time
import logging

from utils.web_site_scraper import PatternScraper
from utils.dict_cleaner_and_writer import DictCleaner
from utils.output_files_formats import CSVCreator
from utils.pprints import PPrints
from threading import Lock

class GoogleMaps:
    _maps_url = "https://www.google.com/maps"
    temp_list = []

    def __init__(self, driver_path: str, unavailable_text: str = "Not Available", headless: bool = False,
                 wait_time: int = 15, suggested_ext: list = None, output_path: str = "./CSV_FILES",
                 verbose: bool = True, result_range: int = None, print_lock: Lock = None):
        if suggested_ext is None:
            suggested_ext = []

        self._unavailable_text = unavailable_text
        self._headless = headless
        self._wait_time = wait_time
        self._wait = None
        self._main_handler = None
        self._suggested_ext = suggested_ext
        self._output_path = output_path
        self._verbose = verbose
        self._results_range = result_range

        self._web_pattern_scraper = PatternScraper()
        self._csv_creator = CSVCreator(output_path=output_path, file_lock=print_lock)
        self._dict_cleaner = DictCleaner(unavailable_data=unavailable_text)
        self._print = PPrints(print_lock=print_lock)
        self._driver_path = driver_path

        self.is_path_available()
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def is_path_available(self):
        if not exists(self._output_path):
            mkdir(self._output_path)

    def create_chrome_driver(self):
        options = Options()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-infobars')
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        # Disable GPU acceleration and use software rendering
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-software-rasterizer")

        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")

        if self._headless:
            options.add_argument("--headless=new")

        driver = Chrome(service=Service(self._driver_path), options=options)
        stealth(driver=driver, languages=["en-US", "en"], vendor="Google Inc.", platform="Win32",
                webgl_vendor="Intel Inc.", renderer="Intel Iris OpenGL Engine", fix_hairline=True,
                run_on_insecure_origins=False)
        self._wait = WebDriverWait(driver, self._wait_time, ignored_exceptions=(NoSuchElementException,
                                                                                StaleElementReferenceException))
        return driver

    @staticmethod
    def load_url(driver, url):
        driver.get(url)

    def search_query(self, query):
        search_box = self._wait.until(EC.presence_of_element_located((By.ID, "searchboxinput")))
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

    def validate_result_link(self, result, driver):
        if result != "continue":
            get_link = result.get_attribute("href")
            driver.execute_script(f'''window.open("{get_link}", "_blank");''')
            driver.switch_to.window(driver.window_handles[-1])
        else:
            get_link = driver.current_url

        try:
            self._wait.until(EC.url_contains("@"))
            lat_lng = driver.current_url.split("@")[1].split(",")[:2]
        except Exception:
            lat_lng = [self._unavailable_text, self._unavailable_text]

        return lat_lng[0], lat_lng[1], get_link

    def get_title(self, result, driver):
        if result != "continue":
            get_link = result.get_attribute("href")
            driver.execute_script(f'''window.open("{get_link}", "_blank");''')
            driver.switch_to.window(driver.window_handles[-1])
        else:
            get_link = driver.current_url
        try:
            title = driver.find_element(By.CSS_SELECTOR, '#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > '
                                                         'div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > '
                                                         'div.lMbq3e > div:nth-child(1) > h1')
            title_text = title.text
        except Exception:
            title_text = self._unavailable_text
        return title_text

    def get_rating_in_card(self, driver):
        try:
            rating = driver.find_element(By.CSS_SELECTOR, '#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div '
                                                          '> div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > '
                                                          'div.lMbq3e > div.LBgpqf > div > div.fontBodyMedium.dmRWX > '
                                                          'div.F7nice > span:nth-child(1) > span:nth-child(1)')
            rating_text = rating.text
        except Exception:
            rating_text = self._unavailable_text
        return rating_text

    def get_website_link(self, driver):
        try:
            website = driver.find_element(By.CSS_SELECTOR, 'div.UCw5gc > div > div:nth-child(1) > a['
                                                           'data-tooltip="Open website"]')
            website_href = website.get_attribute("href")
        except Exception:
            website_href = self._unavailable_text
        return website_href

    def get_phone_number(self, driver):
        try:
            phone = driver.find_elements(By.CLASS_NAME, 'rogA2c')
            phone_href = next((ph.text for ph in phone if ph.text.replace("(", "").replace(")", "").replace(" ", "")
                              .replace("+", "").replace("-", "").isnumeric()), self._unavailable_text)
        except Exception:
            phone_href = self._unavailable_text
        return phone_href

    def get_about_description(self, driver):
        try:
            driver.find_element(By.CSS_SELECTOR, '#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > '
                                                 'div.e07Vkf.kA9KIf > div > div > div:nth-child(3) > div > div > '
                                                 'button:nth-child(3)').click()
            self._wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#QA0Szd > div > div > '
                                                                              'div.w6VYqd > div.bJzME.tTVLSc '
                                                                              '> div > div.e07Vkf.kA9KIf > '
                                                                              'div > div > '
                                                                              'div.m6QErb.DxyBCb.kA9KIf.dS8AEf')))

            about_text = driver.find_element(By.CSS_SELECTOR,
                                             '#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > '
                                             'div > div.e07Vkf.kA9KIf > div > div > '
                                             'div.m6QErb.DxyBCb.kA9KIf.dS8AEf > div.PbZDve > p > '
                                             'span > span').text
            about_dict = {"about_desc": about_text}
        except NoSuchElementException:
            about_dict = {"about_desc": self._unavailable_text}
        return about_dict

    def reset_driver_for_next_run(self, result, driver):
        if result != "continue":
            driver.close()
            driver.switch_to.window(self._main_handler)
            self._wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))

    def scroll_to_the_end_event(self, driver):
        try:
            self._wait.until(EC.presence_of_element_located((By.CLASS_NAME, "hfpxzc")))
        except TimeoutException:
            results = ["continue"]
            return results

        scroll_end = 'div.PbZDve  > p.fontBodyMedium  > span > span[class="HlvSq"]'
        start_time = time()
        scroll_wait = 1
        while True:
            results = driver.find_elements(By.CLASS_NAME, 'hfpxzc')
            if self._results_range and len(results) >= self._results_range:
                results = results[:self._results_range + 1]
                break

            driver.execute_script('arguments[0].scrollIntoView(true);', results[-1])
            driver.implicitly_wait(scroll_wait)
            try:
                text_span = driver.find_element(By.CSS_SELECTOR, scroll_end)
                if "you've reached the end" in text_span.text.lower():
                    break
            except NoSuchElementException:
                pass

            if time() - start_time > 60:
                break

        return results

    def _scrape_result_and_store(self, driver, mode, result, query, results_indices, update_callback, stop_flag, lenn):
        # if stop_flag():
        #     return
        if len(GoogleMaps.temp_list) == lenn:
            return
        temp_data = {}

        # if self._verbose:
        #     self._print.print_with_lock(query=query, status="Getting Latitude and longitude", mode=mode,
        #                                 results_indices=results_indices)
        # map_link = self.validate_result_link(result, driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Getting title", mode=mode, results_indices=results_indices)
        card_title = self.get_title(result,driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Getting rating", mode=mode, results_indices=results_indices)
        card_rating = self.get_rating_in_card(driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Getting WebLink", mode=mode, results_indices=results_indices)
        card_website_link = self.get_website_link(driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Getting WebLink Data", mode=mode, results_indices=results_indices)
        website_data = self._web_pattern_scraper.find_patterns(driver, card_website_link, self._suggested_ext,
                                                               self._unavailable_text)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Getting Phone Number", mode=mode, results_indices=results_indices)
        card_phone_number = self.get_phone_number(driver)

        # if self._verbose:
        #     self._print.print_with_lock(query=query, status="Getting About data", mode=mode, results_indices=results_indices)
        # card_about = self.get_about_description(driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Resetting Driver", mode=mode, results_indices=results_indices)
        self.reset_driver_for_next_run(result, driver)

        if self._verbose:
            self._print.print_with_lock(query=query, status="Storing Data in List", mode=mode, results_indices=results_indices)

        temp_data["title"] = card_title
        # temp_data["map_link"] = map_link
        temp_data["rating"] = card_rating
        temp_data["webpage"] = card_website_link
        temp_data["phone_number"] = card_phone_number
        temp_data.update(website_data)
        # temp_data.update(card_about)

        GoogleMaps.temp_list.append(temp_data)
        update_callback(results_indices[1])

    def start_scrapper(self, query: str, update_callback, stop_flag) -> None:
        mode = "headless" if self._headless else "windowed"
        try:
            if self._verbose:
                self._print.print_with_lock(query=query, status="Initializing Browser", mode=mode)

            driver = self.create_chrome_driver()

            if self._verbose:
                self._print.print_with_lock(query=query, status="Loading URL", mode=mode)

            self.load_url(driver, self._maps_url)

            if self._verbose:
                self._print.print_with_lock(query=query, status="Searching query", mode=mode)

            self.search_query(query)
            self._main_handler = driver.current_window_handle

            if self._verbose:
                self._print.print_with_lock(query=query, status="Loading Links from GMAPS", mode=mode)

            results = self.scroll_to_the_end_event(driver)
            
            result_indices = [len(results), 1]
            for result in results:
                self._scrape_result_and_store(driver=driver, mode=mode, result=result, query=query, 
                                              results_indices=result_indices, update_callback=update_callback, stop_flag=stop_flag, lenn = len(results))
                result_indices[1] += 1
                if len(GoogleMaps.temp_list) == len(results):
                    break
            if self._verbose:
                self._print.print_with_lock(query=query, status="Dumping data in CSV file", mode=mode)
            
            self._csv_creator.create_csv(list_of_dict_data=GoogleMaps.temp_list)        
            
            if self._verbose:
                self._print.print_with_lock(query=query, status="Driver Closed", mode=mode)
            driver.close()
        except NoSuchWindowException:
            if self._verbose:
                self._print.print_with_lock(query=query, status="Browser Closed", mode=mode)
        except Exception as e:
            if self._verbose:
                self._print.print_with_lock(query=query, status=f"Error: {str(e)}", mode=mode)
            self.logger.error(f"An error occurred: {e}") 