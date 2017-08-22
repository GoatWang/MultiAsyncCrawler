import aiohttp
import asyncio
import async_timeout

import queue
import threading

from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd

import string
import json
import os


## Build Queue
input_companies = queue.Queue()
fail_log = queue.Queue()

companies = [
        "Agilysys, Inc.",
        "ASEC International Corporation",
        "Beijing Oriental Jicheng Co Ltd",
        "Chander Electronics Corp.",
        "Dragon Group International Limited",
        "Euro Tech Holdings Company Ltd",
        "Howteh Technology Co., Ltd.",
        "Kyokuto Boeki Kaisha, Ltd.",
        "Leeport (Holdings) Limited",
        "Makus, Inc.",
        "MEIJI ELECTRIC INDUSTRIES CO., LTD.",
        "Naito & Co Ltd",
        "OSAKA KOHKI CO LTD",
        "Premier Farnell plc",
        "Rexel SA",
        "Solomon Technology Corporation",
        "TAKACHIHO KOHEKI CO., LTD.",
        "TOMITA CO., LTD.",
        "Uematsu Shokai Co., Ltd.",
        "Unitron Tech Co Ltd",
        "Vitec Holdings Co Ltd",
        "WPG Holdings Limited",
        "Wuhan P&S Information Technology Co Ltd",
        "Yleiselektroniikka Oyj"
        ]

for company in companies:   
    input_companies.put("{} product".format(company))

class newBingCrawler:
    def __init__(self):
        self.loop = asyncio.new_event_loop()

    def __call__(self):
        async def fetch_coroutine(client, url):
            with async_timeout.timeout(10):
                try: 
                    async with client.get(url) as response:
                        assert response.status == 200
                        if 'html' in str(response.content_type).lower():
                            html = await response.text()
                            soup = BeautifulSoup(html ,'lxml')
                            [x.extract() for x in soup.findAll('script')]
                            [x.extract() for x in soup.findAll('style')]
                            [x.extract() for x in soup.findAll('nav')]
                            [x.extract() for x in soup.findAll('footer')]
                            self.companyInfo += soup.text
                        return await response.release()
                except:
                    self.failLinks.append(url)

        async def main(loop):
            driver = webdriver.PhantomJS()
            url = "https://www.bing.com/"
            driver.get(url)
            elem = driver.find_element_by_xpath('//*[@id="sb_form_q"]')
            elem.send_keys(self.query)
            elem = driver.find_element_by_xpath('//*[@id="sb_form_go"]')
            elem.submit()
            html = driver.page_source
            driver.close()

            soup = BeautifulSoup(html, 'lxml')
            Links = soup.find_all('a')

            # Find links in first page in Bing Search Engine
            Goodlinks = []
            for link in Links:
                linkstr = str(link)
                if (('http' in linkstr) and ('href' in linkstr) and (not 'href="#"' in linkstr) and (not 'href="http://go.microsoft' in linkstr)and (not 'microsofttranslator' in linkstr)):
                    Goodlinks.append(link)
            urls = [link['href'] for link in Goodlinks]

            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
            async with aiohttp.ClientSession(loop=loop, headers=headers, conn_timeout=5 ) as client:
                tasks = [fetch_coroutine(client, url) for url in urls]
                await asyncio.gather(*tasks)
 
        while True:
            try:
                self.query = input_companies.get(timeout=1)   ##Build self.query
            except:
                break
            
            ## build self attr
            self.companyInfo = ""  ##Build self.companyInfo
            exclude = set(string.punctuation)
            companyName = self.query.replace(" product", "")
            companyName = ''.join(p for p in companyName if p not in exclude)
            self.companyName = companyName.replace(" ", "_").lower()  ##Build self.companyName
            self.failLinks = []  ##Build self.failLinks

            ## start running loop
            self.loop.run_until_complete(main(self.loop))

            ## After loop
            fail_log.put({self.companyName:self.failLinks})
            
            if not os.path.isdir("comapnyEmbedding"):
                os.mkdir("comapnyEmbedding")

            file = open("comapnyEmbedding/" + self.companyName, 'w', encoding='utf8')
            file.write(self.companyInfo)
            file.close()

            print("ThreadingID: " + str(id(self)) + ", " + companyName + " success")


threads = []
for i in range(4):
    newthread = threading.Thread(target=newBingCrawler())
    newthread.start()
    threads.append(newthread)

for thread in threads:
    thread.join()

logs = []
while True:
    try:
        logLi = fail_log.get(timeout=1)
        if logLi != []:
            logs.append(logLi)
    except:
        break

with open("FailLinks.log",'w', encoding='utf8') as fp:
    json.dump(logs, fp)