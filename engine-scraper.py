import schedule
import requests
import utm
from bs4 import BeautifulSoup
import logging
import os
import time

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


baseUrl = os.getenv("BASE_URL", "https://earthquake.tmd.go.th/inside.html")
apiUrl = os.getenv("API_URL", "http://192.168.31.230:3000/api/fault-data/record")


def ApiGet():
    res = requests.get(apiUrl)
    res.encoding = "utf-8"
    if res.status_code == 200:
        logging.info(f"Records created successfully! Status code: {res.status_code}")
        return int(res.text)
    else:
        logging.error(f"Failed to create records! Status code: {res.status_code}")
        return -1


def ApiPost(body):
    res = requests.post(apiUrl, json=body)
    if res.status_code == 201:
        logging.info(f"Records created successfully! Status code: {res.status_code}")
    else:
        logging.error(f"Failed to create records! Status code: {res.status_code}")


def checkNewRecord():
    url = f"{baseUrl}?ps=1"
    res = requests.get(url)
    res.encoding = "utf-8"
    if res.status_code == 200:
        logging.info(f"Scrape success! Status codes: {res.status_code}")
    else:
        logging.error(f"Someting wrong! Status code: {res.status_code}")

    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find_all("table")
    pagination = table[2].find_all("b")
    pagination_data = pagination[0].string.split(" ")
    all_data = int(pagination_data[-1])
    print(all_data)
    oldNumber = ApiGet()
    if oldNumber < 0:
        return
    # API calling last number
    if all_data > oldNumber:
        newData = all_data - oldNumber
        scrapeUrl = f"{baseUrl}?ps={newData}&pageNum_thaievent=0"
        scrapeData(scrapeUrl)


def scrapeData(scrapeUrl):
    res = requests.get(scrapeUrl)
    res.encoding = "utf-8"

    if res.status_code == 200:
        logging.info(f"Scrape success! Status code: {res.status_code}")
    else:
        logging.error(f"Someting wrong! Status code: {res.status_code}")

    soup = BeautifulSoup(res.text, "html.parser")

    table = soup.find_all("table")
    dataTable = table[1]
    dataTable = dataTable.find_all("tr")

    if len(dataTable) > 0:
        logging.info(f"New data:{len(dataTable)-1}")
        extractData(dataTable)


def extractData(dataTable):
    tempArr = []
    chunks = []
    tempArr.clear()
    for i in range(len(dataTable) - 1):
        dataTd = dataTable[i + 1].find_all("td")
        coordinate = utm.from_latlon(
            float((str(dataTd[2].string))[0:-2]),
            float((str(dataTd[3].string))[0:-2]),
        )
        pos = (
            (
                str(dataTd[6].select("span")).replace('[<span class="style10">', "")
            ).replace("</span>]", "")
        ).split("<br/>")
        tempData = {
            "dateUtc": str(dataTd[0].p.string)[:-4],
            "magnitude": float(dataTd[1].string),
            "lat": float((dataTd[2].string)[0:-2]),
            "long": float((dataTd[3].string)[0:-2]),
            "utmX": int(coordinate[0]),
            "utmY": int(coordinate[1]),
            "depth": 0 if dataTd[4].string == "-" else float(dataTd[4].string),
            "phase": 0 if dataTd[5].string == "-" else int(dataTd[5].string),
            "centerTh": str(pos[0]),
            "centerEn": str(pos[1]),
        }
        tempArr.append(tempData)
    # ApiPost(tempArr)
    tempArr = tempArr[::-1]
    chunks = [tempArr[i : i + 50] for i in range(0, len(tempArr), 50)]
    # Send each chunk as a separate request
    for chunk in chunks:
        ApiPost(chunk)
        time.sleep(30)


# updateScrapeData(len(dataTable))


checkNewRecord()
schedule.every(30).minutes.do(checkNewRecord)
while True:
    schedule.run_pending()
    time.sleep(1)
