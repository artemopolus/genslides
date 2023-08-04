from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import InvalidSessionIdException

from bs4 import BeautifulSoup

import urllib3
import json


class Browser():
    def __init__(self) -> None:
        pass
    def getData(self, links):
        return ""


class WebBrowser(Browser):
    def __init__(self) -> None:
        super().__init__()
        path_to_config = "config\\base.json"
        with open(path_to_config, 'r') as config:
            values = json.load(config)
            # self.path_to_browser = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            self.path_to_browser = values["web browser"]

    def getData(self, links):
        print("Get data from web browser")
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        options.add_argument("--no-sandbox")
        options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        path = self.path_to_browser
        options.binary_location = path
        out_text = ""
        for i,link in enumerate(links):
            try:
                driver = webdriver.Chrome(options=options)
                print(str(i+1) + " / " + str(len(links)) + '\n' + link)
                # print(link)
                driver.command_executor.set_timeout(60)
                driver.get(url=link)
                page_source = driver.execute_script(
                    "return document.body.outerHTML;")
                print('soup')
                soup = BeautifulSoup(page_source, "html.parser")
                text = soup.get_text()
                out_text += text + '\n'
                print('done=',len(text))
                driver.close()
            except Exception as e:
                print(e)
                # driver.close()
            
        return out_text

    def get(self, link):
        print("Get data from web browser")
        options = Options()
        options.add_argument("start-maximized")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.49 Safari/537.36"
        )
        options.add_argument("--no-sandbox")
        options.add_experimental_option(
            'excludeSwitches', ['enable-logging'])
        path = self.path_to_browser
        options.binary_location = path
        out_text = ""
        try:
            driver = webdriver.Chrome(options=options)
            # print(str(i+1) + " / " + str(len(links)) + '\n' + link)
            print("load by link=",link)
            # driver.command_executor.set_timeout(60)
            driver.get(url=link)
            page_source = driver.execute_script(
                "return document.body.outerHTML;")
            print('soup')
            soup = BeautifulSoup(page_source, "html.parser")
            text = soup.get_text()
            out_text += text
            print('done=',len(text))
            driver.close()
        except Exception as e:
            print("Page opening error=",e)
            driver.close()
        
        return out_text
