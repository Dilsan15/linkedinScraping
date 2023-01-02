
import os
from scraping import jobScraper

# Number of forms needed to be scraped. Keep this number below 988 as this is linkedin's limit for loading more jobs
num_of_jobs_needed = 988

# Timezone
scraping_timezone = "MDT"

# Form website link
basic_link = "https://ca.linkedin.com/"

# Link to a specific category
website_page = "jobs/search?keywords=Machine%20Learning&location=Canada&geoId=101174742&trk=public_jobs_jobs-search-bar_search-submit&position=1&pageNum=0"

# Path to the webdriver, saved as env
driver_path = os.environ["DRIVER_PATH"]  # Todo("CHANGE THIS TO UR PATH! so it looks like driver_path = 'YOUR STRING' ")

# time out needed between events, based on Wi-Fi and PC performance
time_out = 3

# Boolean which controls if the browser activities will be shown on screen on or not
browser_visible = False

if __name__ == "__main__":

    JobScraper = jobScraper(basic_link, website_page, driver_path, num_of_jobs_needed, time_out,browser_visible, scraping_timezone)

    