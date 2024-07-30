from webdriver_manager.chrome import ChromeDriverManager
from utils.threading_controller import FastSearchAlgo
from argparse import ArgumentParser
import tkinter as tk
from tkinter import ttk
from threading import Event, Thread, Lock
import logging
import time

class GMapsScraper:
    def __init__(self):
        self._args = None
        self.setup_logging()
        self.stop_event = Event()
        self.result_count = 0
        self.scraping_thread = None
        self.status_thread = None

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def arg_parser(self):
        parser = ArgumentParser(description='Command Line Google Map Scraper by Abdul Moez')

        # Input options
        parser.add_argument('-l', '--limit', help='Number of results to scrape (-1 for all results, default: 500)',
                            type=int, default=200)
        parser.add_argument('-u', '--unavailable-text',
                            help='Replacement text for unavailable information (default: "Not Available")', type=str,
                            default="Not Available")
        parser.add_argument('-bw', '--browser-wait', help='Browser waiting time in seconds (default: 15)', type=int,
                            default=15)
        parser.add_argument('-se', '--suggested-ext',
                            help='Suggested URL extensions to try (can be specified multiple times)', action='append',
                            default=[])
        parser.add_argument('-wb', '--windowed-browser', help='Disable headless mode', action='store_false',
                            default=True)
        parser.add_argument('-v', '--verbose', help='Enable verbose mode', action='store_true')
        parser.add_argument('-o', '--output-folder', help='Output folder to store CSV details (default: ./CSV_FILES)',
                            type=str, default='./CSV_FILES')
        parser.add_argument('-d', '--driver-path',
                            help='Path to Chrome driver (if not provided, it will be downloaded)', type=str,
                            default='')

        self._args = parser.parse_args()

    def scrape_maps_data(self, query):
        self.result_count = 0
        limit_results = 500 if self._args.limit == -1 else self._args.limit

        driver_path = self._args.driver_path
        if not self._args.driver_path:
            try:
                driver_path = ChromeDriverManager().install()
            except ValueError:
                self.logger.error("Not able to download the driver which is compatible with your browser.")
                self.logger.info("Head to this site (https://chromedriver.chromium.org/downloads)"
                                 " and find your version driver and pass it with argument -d.")
                return

        print_lock = Lock()
        algo_obj = FastSearchAlgo(
            unavailable_text=self._args.unavailable_text,
            headless=self._args.windowed_browser,
            wait_time=self._args.browser_wait,
            suggested_ext=self._args.suggested_ext,
            output_path=self._args.output_folder,
            workers=10,  # Increase number of workers for parallel processing
            result_range=limit_results,
            verbose=self._args.verbose,
            driver_path=driver_path,
            print_lock=print_lock
        )

        def update_result_count(count):
            self.result_count = count
            result_label.config(text=f"Results Scraped: {self.result_count}")
            progress_bar['value'] = (self.result_count / limit_results) * 100
            root.update_idletasks()

        def scrape_with_update():
            try:
                algo_obj.fast_search_algorithm([query], update_result_count, lambda: self.stop_event.is_set())
            except Exception as e:
                self.logger.error(f"Error during scraping: {e}")

        self.scraping_thread = Thread(target=scrape_with_update, daemon=True)
        self.scraping_thread.start()

    def run(self):
        global root
        root = tk.Tk()
        root.title("Google Maps Scraper")
        root.geometry("600x400")
        root.configure(bg='#F0F0F0')  # Light gray background for a modern look

        style = ttk.Style()
        style.configure('TButton',
                        padding=10,
                        relief='flat',
                        font=('Segoe UI', 12, 'bold'))
        
        # Configure the Start Scraper button style
        style.configure('StartButton.TButton',
                        background='#2196F3',  # Blue background
                        foreground='black')
        style.map('StartButton.TButton',
                  background=[('active', '#1976D2')],  # Darker blue on hover
                  foreground=[('active', 'white')])
        
        # Configure the Stop Scraper button style
        style.configure('StopButton.TButton',
                        background='#F44336',  # Red background
                        foreground='black')
        style.map('StopButton.TButton',
                  background=[('active', '#D32F2F')],  # Darker red on hover
                  foreground=[('active', 'white')])
        
        style.configure('TLabel', background='#F0F0F0', foreground='black', font=('Segoe UI', 12, 'bold'))
        style.configure('TEntry', padding=10, relief='flat', font=('Segoe UI', 12))
        style.configure('TProgressbar', troughcolor='#BDBDBD', background='#2196F3', thickness=20)

        frame = ttk.Frame(root, padding=20, style='TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Enter Search Query:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        query_entry = ttk.Entry(frame, width=50)
        query_entry.grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(frame, text="Limit (number of results):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        limit_entry = ttk.Entry(frame, width=10)
        limit_entry.insert(0, "200")  # Default value
        limit_entry.grid(row=1, column=1, padx=10, pady=10)

        global result_label
        result_label = ttk.Label(frame, text="Results Scraped: 0")
        result_label.grid(row=2, columnspan=2, pady=10)

        global progress_bar
        progress_bar = ttk.Progressbar(frame, style='TProgressbar', length=500, mode='determinate')
        progress_bar.grid(row=3, columnspan=2, pady=10)

        status_label = ttk.Label(frame, text="Status: 🚀", font=('Segoe UI', 12, 'bold'))
        status_label.grid(row=4, columnspan=2, pady=10)

        def update_status():
            emojis = ["🚀", "🚀🚀", "🚀🚀🚀", "🚀🚀🚀🚀", "🚀🚀🚀🚀🚀"]
            count = 0
            while not self.stop_event.is_set():
                status_label.config(text=f"Status: {emojis[count % len(emojis)]}")
                count += 1
                root.update_idletasks()
                time.sleep(0.2)  # Reduced sleep time for faster updates

        def on_start_click():
            query = query_entry.get()
            limit = limit_entry.get()
            if query and limit.isdigit():
                self._args.limit = int(limit)
                self.stop_event.clear()
                progress_bar['value'] = 0
                self.scrape_maps_data(query)
                self.status_thread = Thread(target=update_status, daemon=True)
                self.status_thread.start()

        def on_stop_click():
            self.stop_event.set()
            if self.scraping_thread and self.scraping_thread.is_alive():
                self.scraping_thread.join(timeout=10)  # Ensure scraping thread stops
            if self.status_thread and self.status_thread.is_alive():
                self.status_thread.join(timeout=10)  # Ensure status thread stops

        def on_close():
            self.stop_event.set()
            if self.scraping_thread and self.scraping_thread.is_alive():
                self.scraping_thread.join(timeout=10)  # Ensure scraping thread stops
            if self.status_thread and self.status_thread.is_alive():
                self.status_thread.join(timeout=10)  # Ensure status thread stops
            root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_close)

        start_button = ttk.Button(frame, text="Start Scraper", style='StartButton.TButton', command=on_start_click)
        start_button.grid(row=5, column=0, pady=20, sticky=tk.EW)

        stop_button = ttk.Button(frame, text="Stop Scraper", style='StopButton.TButton', command=on_stop_click)
        stop_button.grid(row=5, column=1, pady=20, sticky=tk.EW)

        # Add some padding to the grid cells
        for widget in frame.winfo_children():
            widget.grid_configure(padx=10, pady=5)

        root.mainloop()

if __name__ == '__main__':
    App = GMapsScraper()
    App.arg_parser()
    App.run()
