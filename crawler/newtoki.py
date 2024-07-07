#!/usr/lib/python3.6
import os
import shutil
import zipfile
import sys
import time
import configparser
import multiprocessing
import urllib.request
import time
import cfscrape
from urllib import parse
import telegram
import re




from urllib.parse import quote
from bs4 import *
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

from ImageDownloader import *
from Utils import *


#Setting Telegram
bot = telegram.Bot(token ='531823942:AAHby6AFxgPLGBwfWPaxlcYGa9UL61S8ACg')
chat_id = '@leeyj78_comic'

win_debug = 1

#Setting crawler


if win_debug == 0:
    phantomjspath="/usr/bin/phantomjs"
    mangalistfilepath = "/var/www/html/m.txt"
    workpath = "/home/az001a/MaruCrawler"
else:
    phantomjspath="phantomjs.exe"
    mangalistfilepath = "mangalist.txt"
    workpath = "c:\python36"
    


zippath = []
msgdata = []

# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

class MaruCrawler():
    def __init__(self, processNum = 4):
        self.version = "2.12"
        self.logger = CreateLogger("MaruCrawler")
        self.processNum = processNum
        self.driverPath = os.path.realpath(phantomjspath)
        #self.driverPath =("chromedriver.exe")
        self.opener = webdriver.PhantomJS(executable_path=self.driverPath)
        #self.opener = webdriver.Chrome(self.driverPath)
        self.opener.addheaders = [('User-Agent', "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36")]
        self.mainURL = "https://newtoki.com/comic/" 
        
    
    def Run(self, mangaName):
        # Check files
        self.logger.info("Start Download Manga : %d" % int(mangaName))
        if not os.path.exists(self.driverPath):
            self.logger.error("WebDriverNotFound ( path : %s )" % (self.driverPath))
            return False

        self.mangaName = mangaName
        self.mangaURL    = self.mainURL + str(self.mangaName)
        self.logger.debug("Start Crawling %s" % (self.mangaURL))

        # Get Manga main source
        source = self.Crawl(self.mangaURL)
        if source == False:
            return False
        # Get Manga name
        source = BeautifulSoup(source, "html5lib")
        
        self.manga = source.find('span', {'class','page-desc'})
        
        if self.manga == None:
            self.logger.error("CannotFindManga ( url : %s )" % (self.mangaURL))
            return False
        self.manga = "%s" % (self.manga.text.strip())
        self.manga = ValidateFileName(self.manga)
        self.logger.info("Manga name : %s" % self.manga)
        
        
        # Get Manga Episodes
        self.episodeLists = self.GetEpisodeLists(source)
        if len(self.episodeLists) == 0:
            self.logger.error("NoEpisodes ( url : %s )" % (self.mangaURL))
            return False
            
        print(self.episodeLists)

        # Make Processes
        taskQueue  = multiprocessing.Queue()
        endQueue   = multiprocessing.Queue()
        workerList = []
        for i in range(self.processNum):
            workerList.append(multiprocessing.Process(target = ImageDownloaderRunner, args = (taskQueue, endQueue, )))
            workerList[i].start()

        for episode in self.episodeLists:
            #print(os.path.join(os.path.realpath("Download"), self.manga) +"/" + episode["episodeName"]   + ".zip")
            if os.path.exists(os.path.join(os.path.realpath("Download"), self.manga) +"/" + episode["episodeName"]   + ".zip"):
                self.logger.info("AlreadyExistsEpisode, Skip ( EpisodeName : %s )" % (episode["episodeName"]))
                continue
            zippath.append(os.path.join(os.path.realpath("Download"), self.manga, episode["episodeName"]))
            #msgdata.append(self.manga)
            msgdata.append(episode["episodeName"])

            #print("EpisodeName : %s, URL : %s" % (episode["episodeName"], episode["url"]))
            imageList = self.GetImageLists(episode["episodeName"], episode["url"])
            if imageList == False:
                self.logger.info("Can't download episode ( EpisodeName : %s, URL : %s )" % (episode["episodeName"], episode["url"]))
                continue
            for imageData in imageList:
                taskQueue.put(imageData)

        # Process End Checking
        while True:
            time.sleep(1)
            if endQueue.qsize() >= self.processNum:
                break

        # Kill all workers
        for worker in workerList:
            worker.terminate()

        self.logger.info("Download Completed")
        time.sleep(10)
        return True

    def compress_del(self):
        # compress Zip
        for i in range(len(zippath)):
            self.logger.info("compress zip ..." +  zippath[i] + ".zip")
            if os.path.isdir(zippath[i]):
                bzip = zipfile.ZipFile(zippath[i] + ".zip",'w')
                for foldername, subfolders, filenames in os.walk(zippath[i]):
                    os.chdir(foldername)
                    for file in filenames:
                        bzip.write(file)
                bzip.close()
            else:
                continue
        
        time.sleep(5)
        # remove download dir & files
        os.chdir(os.path.join(downloadpath))
        
        for i in range(len(zippath)):
            self.logger.info("remove : " + zippath[i])
            if os.path.isdir(zippath[i]):
                shutil.rmtree(zippath[i])
            else:
                continue
            
        return True

    def UpdateManga(self):
        self.logger.info("Update Started")
        if not os.path.exists(os.path.realpath("Download")):
            #self.logger.info("DirectoryNotExists ( Dir : %s )" % (os.path.exists(os.path.realpath("Download"))))
            return True

        for subPath, subDirs, subFiles in os.walk(os.path.realpath("Download")):
            for subDir in subDirs:
                mangaName = int(subDir.split("]")[0][1:])
                self.Run(mangaName = mangaName)
            break
            # for 1 depth

        self.logger.info("Update Ended")

    def GetImageLists(self, episodeName, targetURL):
        imageList = []
        
        
        
        # Try 5 times
        caps = DesiredCapabilities.PHANTOMJS
        caps["phantomjs.page.settings.userAgent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"
        driver = webdriver.PhantomJS(self.driverPath, desired_capabilities=caps)
        #driver = webdriver.Chrome(self.driverPath, desired_capabilities=caps)
        driver.set_page_load_timeout(30)  # 60 seconds timeout
        driver.implicitly_wait(10)
        #scraper = cfscrape.CloudflareScraper()
        #source = scraper.get(targetURL).content
        
        driver.get(targetURL)
        #time.sleep(6)
        source = BeautifulSoup(driver.page_source, "html5lib")
                
        currentURL = driver.current_url
        driver.quit()
       
        imgTagList = source.find_all('img')
        
        for imgTagNum in range(len(imgTagList)):
            if imgTagList[imgTagNum].has_attr('data-original'): 
                tmpURL = imgTagList[imgTagNum]['data-original'] 
                imageList.append({"url":tmpURL})

        if len(imageList) == 0:
            for imgTagNum in range(len(imgTagList)):
                if imgTagList[imgTagNum].has_attr('content'):
                    tmpURL = imgTagList[imgTagNum]['content']
                    imageList.append({"url":tmpURL})
                    print(tmpURL)
        
 
        print(imageList)
        imageList = RemoveDuplicate(imageList)
        for imageNum in range(len(imageList)):
            imageList[imageNum]["savePath"] = os.path.join(os.path.realpath("Download"), self.manga, episodeName, "%03d.jpg" % (imageNum + 1))
            imageList[imageNum]["url"] = imageList[imageNum]["url"][:7] + quote(imageList[imageNum]["url"][7:])
        
        

        return imageList
        
    def close_phantomJS(self):
        self.opener.close()
        self.opener.quit()
    

    def GetEpisodeLists(self, source):
        episodeList = []
        aTagList = source.find_all('a',{'class','item-subject'})
        
        p = re.compile('/span>\n(.+?)<span ')
        
        for i in range(len(aTagList)):
            #print(aTagList[i]['href'])
            title = p.search(str(aTagList[i]))
           # print("url : %s title %s" % (aTagList[i]['href'],aTagList[i].get_text().strip()))
            episodeList.append({"episodeName":ValidateFileName(title.group(1).strip()), "url":aTagList[i]['href']})
        return episodeList

    def Crawl(self, targetURL):
        try:
            #self.opener.get(targetURL)
            #scraper = cfscrape.CloudflareScraper()
            #html =  scraper.get(targetURL).content
            self.opener.get(targetURL)
            time.sleep(7) 
            html = self.opener.page_source
        except:
            print("CrawlError ( url : %s )" % (targetURL))
        else:
            return html
        return False    

if __name__ == "__main__":
    mangaName = None
    mangaList   = None
    mlist = []
    mlisttmp= []
    
    f=open(mangalistfilepath, 'r')
    mlisttmp = f.readline().split('|')
    print(mlisttmp)
    mlist = map(int,mlisttmp)
    
    mlist = mlisttmp
    f.close()
    
    
    os.chdir(workpath)
    downloadpath = os.getcwd()
    
    mangaList = mlist

    multiprocessing.freeze_support()
    crawler = MaruCrawler(processNum = 4)
    
    
    for mangaNum in mangaList:
        result = crawler.Run(mangaNum)
        time.sleep(1)
      
        
    crawler.compress_del()
    crawler.close_phantomJS()
    
     #Send Telegram
    textdata = ""
    for i in range(len(zippath)):
        textdata+=(msgdata[i]) + "\n"
    if textdata == "":
        print("not msg")
    else:
        bot.sendMessage(chat_id='@leeyj78_comic_noti', text=textdata + "가 업데이트 되었습니다.")

    
    exit(0)
