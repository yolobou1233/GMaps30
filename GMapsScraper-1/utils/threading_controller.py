from utils.google_maps_scraper import GoogleMaps
from threading import Lock
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

class FastSearchAlgo:
    def __init__(self, driver_path: str, unavailable_text: str = "Not Available", headless: bool = False, wait_time: int = 15,
                 suggested_ext: list = None, output_path: str = "./CSV_FILES", result_range: int = None,
                 workers: int = 1, verbose: bool = True, print_lock: Lock = None) -> None:
        if suggested_ext is None:
            suggested_ext = ["contact-us", "contact"]

        self._unavailable_text = unavailable_text
        self._headless = headless
        self._wait_time = wait_time
        self._suggested_ext = suggested_ext
        self._output_path = output_path
        self._result_range = result_range
        self._verbose = verbose
        self._driver_path = driver_path
        self._print_lock = print_lock

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def fast_search_algorithm(self, query_list: list[str], update_callback, stop_flag):
        maps_obj = GoogleMaps(unavailable_text=self._unavailable_text, headless=self._headless,
                              wait_time=self._wait_time, suggested_ext=self._suggested_ext,
                              output_path=self._output_path, verbose=self._verbose,
                              result_range=self._result_range, driver_path=self._driver_path,
                              print_lock=self._print_lock)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for query in query_list:
                futures.append(executor.submit(self.scrape_query, maps_obj, query, update_callback, stop_flag))

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    self.logger.error(f"An error occurred: {e}")

    def scrape_query(self, maps_obj, query, update_callback, stop_flag):
        try:
            self.logger.info(f"Starting scraper for query: {query}")
            maps_obj.start_scrapper(query, update_callback, stop_flag)
            self.logger.info(f"Scraping completed for query: {query}")
        except Exception as e:
            self.logger.error(f"An error occurred while scraping query '{query}': {e}")
