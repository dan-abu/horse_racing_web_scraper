"""
Scrapes track names, race numbers, race URLs and race time
from Swiftbet Australia for today and tomorrow.
"""
import re
import sys
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta
import asyncio
import aiofiles
from playwright.async_api import async_playwright

class Bookie_Data():
    """Creating class for bookie data"""
    def __init__(self, url: str, scrape_time: str, xpaths_file: str) -> None:
        """Initialising bookie class"""
        self.url = url
        self.df = None
        self._table_count = 0
        self._track_names = []
        self._race_names = {}
        self._race_data = []
        self._file_creation_time = None
        self._scrape_time = scrape_time
        self.xpaths_file = xpaths_file
        self.tomorrows_races_xpath = None
        self._all_race_tables_xpath = None
        self._race_table_xpath = None
        self._race_table_row_xpath = None
        self._race_table_cell_xpath = None
        self._race_table_track_name_xpath = None
        self._race_table_row_track_name_xpath = None
        self._race_category_xpath = None
        self._race_category_columns_xpath = None
        self._race_category_headers_xpath = None

    @staticmethod
    async def load_xpaths(xpaths_file: str) -> None:
        async with aiofiles.open(xpaths_file, 'r') as file:
            lines = await file.readlines()
        return lines
    
    async def set_xpaths(self) -> None:
        """Sets xpath variables"""
        self.tomorrows_races_xpath = lines[0]
        self._all_race_tables_xpath = lines[1]
        self._race_table_xpath = lines[2]
        self._race_table_row_xpath = lines[3]
        self._race_table_cell_xpath = lines[4]
        self._race_table_cell_links_xpath = lines[5]
        self._race_table_cell_link_xpath = lines[6]
        self._race_table_track_name_xpath = lines[7]
        self._race_table_row_track_name_xpath = lines[8]
        self._race_category_xpath = lines[9]
        self._race_category_columns_xpath = lines[10]
        self._race_category_headers_xpath = lines[11]

    @staticmethod
    def parse_time_string(time_str: str) -> int:
        """Converts time string into integer (seconds)"""
        total_seconds = 0
        parts = re.findall(r"(-?\d+)([dhms])", time_str)
        for value, unit in parts:
            value = int(value)
            if unit == "d":
                total_seconds += value * 86400
            elif unit == "h":
                total_seconds += value * 3600
            elif unit == "m":
                total_seconds += value * 60
            elif unit == "s":
                total_seconds += value
        return total_seconds

    def calculate_race_time(self, time_left: int) -> str:
        """Returns actual race time in format"""
        seconds_left = self.parse_time_string(time_left)
        now = dt.now()
        race_time = now + timedelta(seconds=seconds_left)
        return race_time.strftime("%H:%M:%S %Y-%m-%d")

    @staticmethod
    async def get_element_count(page, xpath: str) -> int:
        """Get number of elements in part of webpage"""
        return len(await page.query_selector_all(xpath))

    async def get_all_cell_values(self, page) -> None:
        """Get race times and race links"""
        for i in range(1, self._table_count):
            row_elements = await page.query_selector_all(f"xpath={self._race_table_xpath.format(i=i)}")
            row_count = len(row_elements)
            
            for j in range(1, row_count + 1):
                row_cell_values = []
                cell_elements = await page.query_selector_all(f"xpath={self._race_table_row_xpath.format(i=i, j=j)}")
                cell_count = len(cell_elements)
                
                for k in range(1, cell_count + 1):
                    cell_element = await page.query_selector(f"xpath={self._race_table_cell_xpath.format(i=i, j=j, k=k)}")
                    if cell_element:
                        cell_text = await cell_element.inner_text()
                        if cell_text:
                            if cell_text in ["CLOSED", "ABANDONED"] or "/" in cell_text:
                                row_cell_values.append("")
                            else:
                                race_time = self.calculate_race_time(cell_text)
                                row_cell_values.append(race_time)
                        else:
                            row_cell_values.append("")
                        
                        cell_link_elements = await page.query_selector_all(f"xpath={self._race_table_cell_links_xpath.format(i=i, j=j, k=k)}")
                        if cell_link_elements:
                            cell_link = await page.query_selector(f"xpath={self._race_table_cell_link_xpath.format(i=i, j=j, k=k)}")
                            href = await cell_link.get_attribute("href")
                            row_cell_values.append(href)
                        else:
                            row_cell_values.append("")
                    else:
                        row_cell_values.extend(["", ""])

                self._race_data.append(row_cell_values)

    async def get_track_names(self, page) -> None:
        """Gets track names"""
        for i in range(1, self._table_count):
            row_elements = await page.query_selector_all(f"xpath={self._race_table_track_name_xpath.format(i=i)}")
            row_count = len(row_elements)
            
            for j in range(1, row_count + 1):
                track_name_element = await page.query_selector(f"xpath={self._race_table_row_track_name_xpath.format(i=i, j=j)}")
                if track_name_element:
                    track_name = await track_name_element.inner_text()
                    self._track_names.append(track_name)

    async def get_race_names(self, page) -> None:
        """Get race names"""
        for i in range(1, self._table_count):
            table_race_names = []
            
            race_category_element = await page.query_selector(f"xpath={self._race_category_xpath.format(i=i)}")
            if race_category_element:
                race_category = await race_category_element.inner_text()
                
                column_elements = await page.query_selector_all(f"xpath={self._race_category_columns_xpath.format(i=i)}")
                column_count = len(column_elements)
                
                for j in range(1, column_count + 1):
                    race_name_element = await page.query_selector(f"xpath={self._race_category_headers_xpath.format(i=i, j=j)}")
                    if race_name_element:
                        race_name = await race_name_element.inner_text()
                        table_race_names.append(race_name)
                
                self._race_names[race_category] = table_race_names

    def create_df(self) -> None:
        """Creates DataFrame from scraped data"""
        cols = max([value for value in self._race_names.values()], key=len)
        race_info = ["Time", "Link"]
        new_cols = pd.MultiIndex.from_product([cols, race_info])
        self.df = pd.DataFrame(data=self._race_data, index=self._track_names, columns=new_cols)

async def scrape(bookies: Bookie_Data, page) -> None:
    """Scrapes web data. Can be extended to include functions that scrape other bits of data"""
    bookies._table_count = await bookies.get_element_count(xpath=bookies._all_race_tables_xpath, page=page) + 1 #counting number of tables (i.e. race categories), add one because of future use of range(1, bookies._table_count)
    await bookies.get_track_names(page=page)
    await bookies.get_race_names(page=page)
    await bookies.get_all_cell_values(page=page)

async def main(url: str, day_check: str, xpaths_file: str) -> None:
    async with async_playwright() as p:
        global lines
        start_time = dt.now()
        browser = await p.chromium.launch()
        page = await browser.new_page()

        url = url
        day_check = day_check
        scrape_time = dt.now()
        xpaths_file = xpaths_file
        bookies = Bookie_Data(url=url, xpaths_file=xpaths_file, scrape_time=scrape_time)
        lines = await bookies.load_xpaths(xpaths_file=xpaths_file)
        await bookies.set_xpaths()

        await page.goto(url)
        await asyncio.sleep(20)

        if day_check == "tomorrow":
            await page.click(bookies.tomorrows_races_xpath)
            await asyncio.sleep(20)

        try:
            await scrape(bookies=bookies, page=page)
        except Exception as e:
            print(e)
            try:
                await scrape(bookies=bookies, page=page)
            except Exception as e:
                print(e)
                print('Failed to scrape on second attempt. Inspect script. Closing programme.')
                sys.exit()

        bookies._file_creation_time = dt.now().strftime("%Y-%m-%d_%H%M%S")
        bookies.create_df()

        if day_check == "tomorrow":
            async with aiofiles.open(f"data/tomorrow/all_races/tomorrow_races_data{bookies._file_creation_time}.csv", mode='w') as f:
                await f.write(bookies.df.to_csv(header=True, index=True))
        else:
            async with aiofiles.open(f"data/today/all_races/today_races_data{bookies._file_creation_time}.csv", mode='w') as f:
                await f.write(bookies.df.to_csv(header=True, index=True))

        await browser.close()
        end_time = dt.now()
        run_time = end_time - start_time
        print("New 'all_races' file downloaded. Run time: ", run_time)

if __name__ == "__main__":
    asyncio.run(main())