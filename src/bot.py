"""
Scrapes current market prices for horses participating in
a selected race
"""
import time
import random
import os
import asyncio
import pandas as pd
from datetime import datetime as dt
from playwright.async_api import async_playwright
import scraper
import sys

class Race_Scraper():
    """Class for scraping prices for a particular race"""
    def __init__(self, csv: str, xpaths_file: str) -> None:
        """Initialising scraper"""
        self.csv = csv
        self.xpaths_file = xpaths_file
        self.races = None
        self.random_race = None
        self.random_race_name = None
        self.headers = []
        self.indexes = []
        self.prices = []
        self.race_headers_count = 0
        self.race_row_count = 0
        self.race_column_count = 0
        self.prices_df = None
        self.headers_xpaths = None
        self.index_xpaths = None
        self.race_column_xpaths = None
        self.race_cell_xpaths = None
        self.race_header_xpaths1 = None
        self.race_header_xpaths2 = None
        self.tomorrows_xpath = None
        self.race_row_xpaths = None

    async def set_xpaths(self) -> None:
        """Sets xpath variables"""
        self.headers_xpaths = lines2[0]
        self.index_xpaths = lines2[1]
        self.race_column_xpaths = lines2[2]
        self.race_cell_xpaths = lines2[3]
        self.race_header_xpaths1 = lines2[4]
        self.race_header_xpaths2 = lines2[5]
        self.tomorrows_xpath = lines2[6]
        self.click_race_xpath = lines2[7]
        self.number_race_xpath1 = lines2[8]
        self.number_race_xpath2 = lines2[9]
        self.race_row_xpaths = lines2[10]

    async def csv_to_df(self) -> None:
        """Turn given CSV into DF"""
        self.races = pd.read_csv(self.csv, header=[0, 1], index_col=[0])

    async def get_random_race(self) -> None:
        """Randomly select race from csv"""
        race_info = ["Time", "Link"]
        place_holder = ["Placeholder"]
        self.random_race = pd.DataFrame(
            index=["Placeholder"],
            columns=pd.MultiIndex.from_product([place_holder, race_info]),
        )

        random_track = self.races.sample(n=1, axis=0)
        track_name = random_track.index[0]

        og_cols = list(random_track.columns)
        new_cols = []
        for col in og_cols:
            new_cols.append(col[0])
        new_cols = set(new_cols)
        new_cols = list(new_cols)

        name_random_race = random.choice(new_cols)
        df_name_random_race = [name_random_race]
        self.random_race.index = random_track.index
        new_col = pd.MultiIndex.from_product([df_name_random_race, race_info])
        self.random_race.columns = new_col

        self.random_race.loc[track_name, (name_random_race, "Time")] = random_track.loc[
            track_name, (name_random_race, "Time")
        ]
        self.random_race.loc[track_name, (name_random_race, "Link")] = random_track.loc[
            track_name, (name_random_race, "Link")
        ]

        self.random_race_name = self.random_race.index[0]

    async def get_random_race_with_timeout(self, timeout: int=60) -> pd.DataFrame:
        """Calling getRandomRace with a timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            await self.get_random_race()
            if not pd.isna(self.random_race.iloc[0, 0]):
                return
        print("Function get_random_race did not successfully complete within 1 minute. Ending bot process.")
        sys.exit()

    async def get_headers(self, page) -> None:
        """Get market price headers"""
        headers_element = await page.query_selector(self.headers_xpaths)
        self.headers = await headers_element.text_content()
        self.headers = self.headers.split(")")
        del self.headers[-1]

    async def get_index(self, page) -> None:
        """Get market price Index"""
        for i in range(1, self.race_row_count, 2):
            index_element = await page.query_selector(self.index_xpaths.format(i=i))
            self.indexes.append(await index_element.text_content())

    async def get_prices(self, page) -> None:
        """Get market prices"""
        self.race_column_count = await scraper.Bookie_Data.get_element_count(page=page, xpath=self.race_column_xpaths) + 1
        for i in range(1, self.race_row_count, 2):
            row_prices = []
            for j in range(2, self.race_column_count):
                column_price_element = await page.query_selector(self.race_cell_xpaths.format(i=i, j=j))
                column_price_text = await column_price_element.text_content()
                row_prices.append(column_price_text)
            self.prices.append(row_prices)

    async def get_race_header_count(self, page) -> None:
        """Returns number of races for a given track"""
        try:
            self.race_headers_count = await scraper.Bookie_Data.get_element_count(page=page, xpath=self.race_header_xpaths1)
        except Exception as e:
            print(e)
            try:
                self.race_headers_count = await scraper.Bookie_Data.get_element_count(page=page, xpath=self.race_header_xpaths2)
            except Exception as e:
                print(e)
                raise e

async def load_random_race(web_scraper: Race_Scraper) -> None:
    """Handles loading random race"""
    await web_scraper.set_xpaths()
    await web_scraper.csv_to_df()
    await web_scraper.get_random_race_with_timeout()

async def scrape(web_scraper: Race_Scraper, page) -> None:
    """Scrapes web data"""
    number_race_name = web_scraper.random_race.columns[0][0][5:]
    await web_scraper.get_race_header_count(page)

    if web_scraper.race_headers_count >= 8:
        await page.click(web_scraper.number_race_xpath1.format(number_race_name=number_race_name))
    else:
        await page.click(web_scraper.number_race_xpath2.format(number_race_name=number_race_name))

    await page.wait_for_timeout(20000)

    web_scraper.race_row_count = await scraper.Bookie_Data.get_element_count(page=page, xpath=web_scraper.race_row_xpaths) + 1

    await web_scraper.get_headers(page)
    await web_scraper.get_index(page)
    await web_scraper.get_prices(page)

async def get_most_recent_file(directory, delay=5):
    # for attempt in range(max_retries):
    while True:
        # Get all files in the directory
        files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        
        if files:
            # Get the most recent file
            most_recent_file = max(files, key=os.path.getctime)
            print("Retrieved latest race data.")
            print("Scraping 'specific_race' data...")
            return most_recent_file
        else:
            print(f"No race data yet. Retrying in {delay} seconds...")
            await asyncio.sleep(delay)
    
async def main(csv_dir: str, day_check: str, xpaths_file: str, url: str) -> None:
    """Programme entry point"""
    global lines2
    start_time = dt.now()
    csv_dir = csv_dir
    csv = await get_most_recent_file(directory=csv_dir)
    day_check = day_check
    xpaths_file = xpaths_file
    url = url

    race_scraper = Race_Scraper(csv=csv, xpaths_file=xpaths_file)

    lines2 = await scraper.Bookie_Data.load_xpaths(xpaths_file=xpaths_file)

    await load_random_race(race_scraper)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        await page.wait_for_timeout(10000)

        race_scraper.race_row_count = await scraper.Bookie_Data.get_element_count(page=page, xpath=race_scraper.race_row_xpaths) + 1

        if day_check == "tomorrow":
            # Tomorrow's webpage
            await page.click(race_scraper.tomorrows_xpath)
            await page.wait_for_timeout(10000)
    
        await page.click(race_scraper.click_race_xpath.format(race_name=race_scraper.random_race_name))

        await scrape(web_scraper=race_scraper, page=page)

        file_creation_time = dt.now().strftime("%Y-%m-%d_%H%M%S")

        bets = pd.DataFrame(data=race_scraper.prices, index=race_scraper.indexes, columns=race_scraper.headers)

        if day_check == "tomorrow":
            bets.to_csv("data/tomorrow/specific_races/staging_bets.csv")
            df_performed_bets = pd.read_csv("data/tomorrow/specific_races/staging_bets.csv", header=0, index_col=0)
            df_performed_bets.dropna(inplace=True)
            df_performed_bets.to_csv(f"data/tomorrow/specific_races/tomorrow_{race_scraper.random_race_name}_{file_creation_time}.csv")
            os.remove("data/tomorrow/specific_races/staging_bets.csv")
        else:
            bets.to_csv("data/today/specific_races/staging_bets.csv")
            df_performed_bets = pd.read_csv("data/today/specific_races/staging_bets.csv", header=0, index_col=0)
            df_performed_bets.dropna(inplace=True)
            df_performed_bets.to_csv(f"data/today/specific_races/today_{race_scraper.random_race_name}_{file_creation_time}.csv")
            os.remove("data/today/specific_races/staging_bets.csv")

        await browser.close()
        end_time = dt.now()
        run_time = end_time - start_time
        print("New 'specific_race' file downloaded. Run time: ", run_time)

if __name__ == "__main__":
    asyncio.run(main())