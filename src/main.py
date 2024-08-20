"""
Runs the scraper.py and bot.py scripts for 5 mins.
"""
import multiprocessing
import time
import asyncio
import sys
import scraper
import bot
import os

def run_scraper(scraper_args):
    while True:
        asyncio.run(scraper.main(**scraper_args))

def run_bot(bot_args):
    asyncio.run(bot.main(**bot_args))

def parse_arguments():
    if len(sys.argv) != 7:
        print("Usage: python main.py <url> <day_check> <scraper_xpaths_file> <bot_xpaths_file> <bot_csv_dir> <specific_races_dir>")
        sys.exit(1)
    
    return {
        "scraper_args": {
            "url": sys.argv[1],
            "day_check": sys.argv[2],
            "xpaths_file": sys.argv[3]
        },
        "bot_args": {
            "url": sys.argv[1],
            "day_check": sys.argv[2],
            "xpaths_file": sys.argv[4],
            "csv_dir": sys.argv[5]
        },
        "specific_races_dir": sys.argv[6]
    }

def main():
    args = parse_arguments()

    # Create a process for the scraper
    scraper_process = multiprocessing.Process(target=run_scraper, args=(args["scraper_args"],))
    scraper_process.start()

    start_time = time.time()
    duration = 300  # 5 minutes in seconds

    while time.time() - start_time < duration:
        # Run bot after scraper completes
        bot_process = multiprocessing.Process(target=run_bot, args=(args["bot_args"],))
        bot_process.start()
        bot_process.join()  # Wait for bot to finish before starting next iteration

    # Terminate the scraper process after 5 minutes
    scraper_process.terminate()
    scraper_process.join()

    # Validating if 'specific_race' files were created
    files = [os.path.join(args["specific_races_dir"], f) for f in os.listdir(args["specific_races_dir"]) if os.path.isfile(os.path.join(args["specific_races_dir"], f))]
    
    if not files:
        print("No 'specific_race' files were created.\nIt appears there are no more races today.\nDouble-check the CSV file.\n")

if __name__ == "__main__":
    main()