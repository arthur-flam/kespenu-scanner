import re

import httpx
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from bs4 import BeautifulSoup


col_attr = {
    0: "link",
    1: "updated_time", # WTF month-first: 9/5/2021 2:01:00 AM
    2: "filesize", # human readable: 12.44 KB
    3: "filetype", # GZ
    4: "category", # lowercase
    5: "location",
    6: "filestem", # filename without extension
    7: "id",
}
def rows_data(index_page: str):
    soup = BeautifulSoup(index_page, 'html.parser')
    for row in soup.find("tbody").find_all("tr"):
        data = {}
        for col_idx, col in enumerate(row.find_all("td")):
            if col_idx == 0:
                attr = col.a.get('href')
            else:
                attr = col.get_text()
            data[col_attr[col_idx]] = attr
        yield data


from models import DataFileType
def store_url(store_id: int, type: DataFileType) -> str:
    r = httpx.get(
        "http://prices.shufersal.co.il/FileObject/UpdateCategory",
        params={
            "catID": type.value,
            "storeId": store_id,
            # "page": page,
            # sort=Time&sortdir=DESC
        },
        timeout=10,
    )
    return list(rows_data(r.text))[0]['link']


def clean(string):
    return re.sub('\s+', ' ', string.strip())

db_path = './shufersal.sqlite'
from db import make_db
shufersal_db = make_db(db_path)


def product_details(barcode: str, no_cache=False):
    if barcode in shufersal_db and not no_cache:
        return shufersal_db[barcode]
    # TODO: store the html somewhere to avoid having to re-fetch it
    #       if we find a way to extra more data 
    url =   f"https://www.shufersal.co.il/online/he/p/P_{barcode}/json"
    r = httpx.get(url, params={"cardContext[openFrom]": "CATEGORY"}, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    data = {}
    images = soup.find_all("img", itemprop="image")
    data['images'] = [i.get('src') for i in images]
    details = soup.find("li", id="techDetails")
    # data['details'] = details
    ingredients = soup.find('div', {"class": "componentsText"})
    if ingredients:
        data['ingredients'] = clean(ingredients.get_text())
    components = soup.find('div', {"class": "featuresList"})
    if components:
        data['components'] = clean(components.get_text())
    warnings = soup.find('li', {"class": "productSymbols"})
    if warnings:
        images = warnings.find_all("img")
        data['warnings'] = [i.get('src') for i in images]
        # data['warnings'] = [i.get('alt') for i in images] # == "red.symbol.classfication.320"
        # 320 => sodium
        # 321 => sugar
        # 322 => fat
    shufersal_db[barcode] = data
    shufersal_db.commit()
    return data

