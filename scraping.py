import time
from datetime import datetime

import pandas as pd
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

            self.link_stored.extend([hidLink.get_attribute('href') for hidLink in
                                     self.driver.find_elements(By.CLASS_NAME, "base-card__full-link")])
            self.link_stored = list(dict.fromkeys(self.link_stored))

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.time_out)

            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if old_height == new_height:

                self.driver.find_element(By.XPATH, '//*[@id="main-content"]/section[2]/button').click()
                time.sleep(self.time_out)

            elif len(self.link_stored) == 988:
                break

            print(str(len(self.link_stored)) + " / " + str(self.links_needed))

        if len(self.link_stored) >= self.links_needed:
            self.link_stored = self.link_stored[:self.links_needed]
        print("final" + str(len(self.link_stored)) + "/" + str(self.links_needed))
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

                    jobData['Title'] = self.driver.find_element(By.XPATH,
                                                                '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h1').text
                    jobData['Url'] = self.driver.current_url
                    jobData['date-scraped'] = f"{datetime.now()} {self.timezone}"
                    jobData['relative-posted-time'] = self.driver.find_element(By.XPATH,
                                                                               '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[2]/span[1]').text

                    jobData['Company'] = self.driver.find_element(By.XPATH,
                                                                  '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[1]/span[1]/a').text
                    jobData['Location'] = self.driver.find_element(By.XPATH,
                                                                   '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[1]/span[2]').text

                    try:
                        jobData['applicant-num'] = self.driver.find_element(By.XPATH,
                                                                            '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[2]/span[2]').text
                    except:
                        jobData['applicant-num'] = self.driver.find_element(By.XPATH,
                                                                            '//*[@id="main-content"]/section[1]/div/section[2]/div/div[1]/div/h4/div[2]/figure/figcaption').text

                    try:
                        jobData['Seniority'] = self.driver.find_element(By.XPATH,
                                                                        '//*[@id="main-content"]/section[1]/div/div/section[1]/div/ul/li[1]/span').text
                    except:
                        print("No Seniority")
                        jobData["Seniority"] = "None"

                    try:
                        jobData['Employment-type'] = self.driver.find_element(By.XPATH,
                                                                              '//*[@id="main-content"]/section[1]/div/div/section[1]/div/ul/li[2]/span').text

                    except:
                        print("no Employment-type")
                        jobData['Employment-type'] = "None"

                    try:
                        jobData['Job-Function'] = self.driver.find_element(By.XPATH,
                                                                           '//*[@id="main-content"]/section[1]/div/div/section[1]/div/ul/li[3]/span').text
                    except:
                        print("no job function")
                        jobData['Job-Function'] = "None"

                    try:
                        jobData['Industries'] = self.driver.find_element(By.XPATH,
                                                                         '//*[@id="main-content"]/section[1]/div/div/section[1]/div/ul/li[4]/span').text
                    except:
                        jobData['Industries'] = "None"

                    jobData['Description'] = self.driver.find_element(By.XPATH,
                                                                      '//*[@id="main-content"]/section[1]/div/div/section[1]/div/div/section/div').text

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
        df.to_csv('data/canadaMachineLearningJobData.csv', mode='w', index=False)
        print("Data Saved")
        print(df)
