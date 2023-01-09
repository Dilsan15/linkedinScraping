import time
from datetime import datetime, timedelta

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By


class jobScraper:

    # On initialization, the class will be given the following parameters
    def __init__(self, basic_link, website_page, driver_path, links_needed, time_out, broswer_vis, timezone):

        self.links_needed = links_needed
        self.website_page = website_page
        self.current_link = basic_link + website_page
        self.driver_path = driver_path
        self.time_out = time_out
        self.timezone = timezone

        self.link_stored = list()

        sel_service = Service(self.driver_path)
        option = webdriver.ChromeOptions()

        if not broswer_vis:
            option.add_argument("--headless")

        self.driver = webdriver.Chrome(service=sel_service, options=option)
        self.driver.get(f'{self.current_link}')

        self.getJobPostings()
        self.saveToCsv(self.getJobData())

    def getJobPostings(self):
        """
        Will get the job postings from the website and append them to a list of links. There is a limit to how many links
        linkedin show you on a page, which is 988
        """

        while len(self.link_stored) < self.links_needed:

            time.sleep(self.time_out)

            old_height = self.driver.execute_script("return document.body.scrollHeight")
            old_num = len(self.link_stored)

            self.link_stored.extend([hidLink.get_attribute('href') for hidLink in
                                     self.driver.find_elements(By.CLASS_NAME, "base-card__full-link")])
            self.link_stored = list(dict.fromkeys(self.link_stored))

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.time_out)

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if old_height == new_height:

                if old_num == len(self.link_stored):
                    break

                self.driver.find_element(By.CLASS_NAME, 'infinite-scroller__show-more-button').click()
                time.sleep(self.time_out)




            print(str(len(self.link_stored)) + " / " + str(self.links_needed))

        if len(self.link_stored) >= self.links_needed:
            self.link_stored = self.link_stored[:self.links_needed]
        print("final" + str(len(self.link_stored)) + " /" + str(self.links_needed))
        # ^^ Will indicate how many links have  been scraped so far

    def getJobData(self):
        """Gets every bit of information provided from a job link and stores it in a list of dictionaries"""
        allJobData = list()

        for jobPost in self.link_stored:
            jobData = {}
            time.sleep(self.time_out)
            self.driver.get(jobPost)

            while self.driver.current_url != jobPost:  # if we run into an authwall
                if self.driver.current_url == "https://www.linkedin.com/in/unavailable/":  # If the link is broken
                    break

                self.driver.get(jobPost)
                time.sleep(self.time_out)

            while True:  # Helps us dodge 403 pages and re-attempt if we run into them. 403 pages occur due to linkedin's
                # anti-scraping measures
                try:

                    bSoup = BeautifulSoup(self.driver.page_source, 'html.parser')

                    jobData['Title'] = bSoup.find('h1', {'class': 'top-card-layout__title'}).text
                    jobData['Url'] = self.driver.current_url
                    jobData['Date-Scraped'] = f"{datetime.now()} {self.timezone}"

                    date_posted = bSoup.find('span', {'class': 'posted-time-ago__text'}).text

                    if "hour" or "minute" in date_posted:
                        jobData["Date-Posted"] = datetime.now().strftime("%Y-%m-%d")

                    elif "day" in date_posted:
                        jobData["Date-Posted"] = (
                                datetime.now() - timedelta(days=int(date_posted[0:1].strip()))).strftime(
                            "%Y-%m-%d")

                    else:
                        jobData["Date-Posted"] = (
                                datetime.now() - timedelta(days=(int(date_posted[0:1].strip()))) * 7).strftime(
                            "%Y-%m-%d")

                    jobData['Company'] = bSoup.find('a', {
                        'class': 'topcard__org-name-link topcard__flavor--black-link'}).text
                    jobData['Location'] = bSoup.find('span', {'class': 'topcard__flavor topcard__flavor--bullet'}).text


                    try:
                        jobData['applicant-num'] = bSoup.find('figcaption', {'class': 'num-applicants__caption'}).text

                    except AttributeError:
                        jobData['applicant-num'] = bSoup.find('span', {'class': 'num-applicants__caption'}).text

                    # Default Values

                    criteria_dict = {"Seniority": "N/A",
                                     "Employment Type": "N/A",
                                     "Job Function": "N/A",
                                     "Industry": "N/A"}

                    criteria_list = bSoup.find('ul', {'class': 'description__job-criteria-list'}).find_all('li')

                    try:
                        criteria_dict['Seniority'] = criteria_list[0].find('span',
                                                                           {
                                                                               'class': 'description__job-criteria-text'}).text
                    except:
                        print("No Seniority")

                    try:
                        jobData['Employment-type'] = criteria_list[1].find('span', {
                            'class': 'description__job-criteria-text'}).text
                    except:
                        print("no Employment-type")

                    try:
                        jobData['Job-Function'] = criteria_list[2].find('span', {
                            'class': 'description__job-criteria-text'}).text
                    except:
                        print("no job function")

                    try:
                        jobData['Industries'] = criteria_list[3].find('span',
                                                                      {'class': 'description__job-criteria-text'}).text
                    except:
                        print("no industries")

                    jobData['Description'] = bSoup.find('div', {'class': 'show-more-less-html__markup'}).text

                    print(jobData)
                    break

                except Exception as e:
                    print(e)
                    time.sleep(30)
                    self.driver.get(jobPost)

            allJobData.append(jobData)
            print((str(self.link_stored.index(jobPost) + 1) + " / " + str(self.links_needed)))  # Indicates progress

        return allJobData

    def saveToCsv(self, data):
        """"Saves the data to a csv file and overwrites any previous data"""

        df = pd.DataFrame(data)
        df.to_csv('data/machineLearningJobData.csv', mode='w', index=False)
        print("Data Saved")
        print(df)
