# Betting Web Scraper

--------------------------------------------------------------------------------------------------------------------------------

## Summary

This package scrapes horse racing times and links from Swiftbet for today and tomorrow's races. This project is purely for
learning purposes. The data is written to disk consistently for five minutes.

While this is happening, the package uses the latest horse racing times and links to randomly scrape
a horse race's odds and write them to disk. This process occurs consistently for five minutes.

All data scraped by these processes gets stored as a CSV.
As part of this repo, a `data/` directory has already been set up to store any data downloaded from the processes.

Xpaths are used as part of the web scraping processes.
You will find the necessary xpaths in `assets/`.
Keep in mind that websites often change their architecture, and so you might need to update the xpaths
and the source code.

--------------------------------------------------------------------------------------------------------------------------------

## Method

`src/main.py` handles the two processes mentioned above. The `multiprocessing` library is used to execute both processes
in parallel.

`src/scraper.py` executes the scraping of the horse racing times and links. `Playwright` is used for web browsing and
`asyncio` is used to make the process asynchronous. You will find that all website data is stored in the `Bookie_data()` class
as well as most methods.

`src/bot.py` runs the scraping of individual horse-racing odds. Similar libraries to those used in `src/scraper.py` are used
here. This script is also asynchronous. You will find another class: `Race_Scraper()`, which contains information known
about a race before and after scraping, as well as most of the methods to scrape the data.

--------------------------------------------------------------------------------------------------------------------------------

## Requirements

We are using `Poetry` to manage dependencies. You will find more
information about the dependencies in `pyproject.toml`.

If you don't have `Poetry` installed, you can install it
following these instructions: `https://python-poetry.org/docs/`.

Once the repo's cloned and `Poetry`'s installed, run
`poetry install` in the CLI to install all the dependencies.

Make sure you have the latest browsers required by `playwright` before kicking off the process. Do this by running
`playwright install`.

When running the script for the first time, you will need to give `playwright` permission
to run a browser in the background. A pop-up will appear asking you to do this the first time you execute the process.

Below you will find two example CLI commands for running the package.
The key differences are in the `<day_check>` args (`today` and `tomorrow`), as well as the directory args at the end of the
commands. These differences allow you to clarify which day's data you want to scrape.

```
poetry run python3 src/main.py https://www.swiftbet.com.au/racing today assets/scraper_xpaths.txt assets/bot_xpaths.txt data/today/all_races data/today/specific_races
poetry run python3 src/main.py https://www.swiftbet.com.au/racing tomorrow assets/scraper_xpaths.txt assets/bot_xpaths.txt data/tomorrow/all_races
```

--------------------------------------------------------------------------------------------------------------------------------

## Watch outs

Given that these are Australian markets (I'm based in the UK), I recommend running these scripts first thing in the morning
to make the most of this package.

If the Swiftbet website undergoes significant design changes, these scripts will need to be updated, so please keep
this in mind.

A common error is `bot.get_random_race` not successfully completing within 1 minute.
This is usually because there are no more races for "today" as per the `today_races_data` file.
If this happens, the programme will continue to download `all_races` data unless you manually stop the programme with `Ctrl + C` in the terminal.
If you let the programme run to completion, despite the `bot.get_random_race` issue, the final message shown at the end of the programme will
confirm if this issue prevented `specific_race` files being created.

**HAPPY WEBSCRAPING**