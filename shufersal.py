import os
import re
import json
from pathlib import Path

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


def barcode_metadata(barcode: str, no_cache=False):
    if barcode in shufersal_db and not no_cache:
        return shufersal_db[barcode]

    cache_dir = Path(os.environ.get('KASPENU_CACHE_DIR', '.cache')) / 'shufersal'
    cache_dir.mkdir(exist_ok=True, parents=True) # TODO: more to init
    cache_path = cache_dir / f'P_{barcode}.html'
    if cache_path.exists():
        print(f'HIT {cache_path}')
        # FIXME: on windows it's a mess, we should not encoding= 
        text = cache_path.read_text(encoding='utf-8', errors='surrogateescape')
    else:
        url = f"https://www.shufersal.co.il/online/he/p/P_{barcode}/json"
        print(f"MISS {url}")
        r = httpx.get(url, params={"cardContext[openFrom]": "CATEGORY"}, verify=False)
        r.raise_for_status()
        if "Forcepoint" in r.text: raise ValueError("Forcepoint")
        if "Shufersal - Error" in r.text: raise ValueError("Error from Shufersal - doenst want us to scrap...")
        if not r.text: raise ValueError("Empty")
        text = r.content
        cache_path.write_bytes(text)

    # TODO: align with https://wiki.openfoodfacts.org/API/Full_JSON_example
    data = {}

    soup = BeautifulSoup(text, 'html.parser')

    element = soup.find("div", {"class": "modal-dialog"})
    meta_str = element.get('data-gtm', '{}')
    meta = json.loads(meta_str)
    # print(meta)
    data["name"] = meta["productName"] # nescafe capuccino classic vanilla
    data["brand"] = meta["brand"] # nestle
    data["categoryID"] = meta["categoryID"] # A130504
    data["categoryCodes"] = meta["categoryCodes"] # ["A","A13","A1305","A130504"]
    # TODO: crawl those once and for all...
    data["categoryLevel1"] = meta["categoryLevel1"] # supermarket
    data["categoryLevel2"] = meta["categoryLevel2"] # drinks, alcohol, wine
    data["categoryLevel3"] = meta["categoryLevel3"] # coffee and tea
    data["categoryLevel4"] = meta["categoryLevel4"] # soluble coffee, chocolate mix...

    images = soup.find_all("img", itemprop="image")
    data['images'] = [i.get('src') for i in images]

    remarks = soup.find('div', {"class": "remarksText"})
    if remarks:
        data['description'] = remarks.get_text("\n", strip=True)

    remap = {
        "מותג/יצרן": "producer_name",
        "ארץ ייצור": "producer_country",
        "כשרות": "kosher_authority", # OU
        "חלבי/בשרי/פרווה": "kosher_type", # חלבי
        "פסח": "kosher_pessah", # לא לפסח
    }
    misc_root = soup.find("ul", {"class": "dataList"})
    if misc_root:
        misc_meta = {}
        for e in misc_root.find_all('li'):
            key = e.find("div", {"class": "name"}).text.replace(":", "")
            if key in ('מק"ט', 'מידה/סוג'):
                continue
            value = e.find("div", {"class": "text"}).text
            misc_meta[remap.get(key, key)] = value
        # print(misc_meta)
        data.update(misc_meta)

    ingredients = soup.find('div', {"class": "componentsText"})
    if ingredients:
        data['ingredients'] = clean(ingredients.get_text())

    allergens = soup.find('div', {"class": "alergiesProperties"})
    if allergens:
        data['allergens'] = clean(allergens.get_text())
    allergens_traces = soup.find('div', {"class": "alergiesTracesProperties"})
    if allergens_traces:
        data['allergens_traces'] = clean(allergens_traces.get_text())
    components = soup.find('div', {"class": "featuresList"})
    if components:
        data['components'] = clean(components.get_text())
    markings = soup.find('div', {"class": "markingList"})
    if markings:
        data['health'] = [
            e.find('div', {"class": "text"}).text
            for m in markings.find_all('div', {"class": "markingItem"}) 
        ]

    product_info = soup.find('ul', {"class": "productContainer"})
    for li in product_info.find_all('li'):
        nutrition_title = li.find('div', {"id": "nutritionListTitle"})
        if nutrition_title:
            if 'nutrition' not in data:
                data["nutrition"] = {}
            serving = clean(li.find('div', {"class": "subInfo"}).get_text())
            data["nutrition"][serving] = []
            for el in li.find('div', {"class": "nutritionList"}).find_all('div', {"class": "nutritionItem"}):
                unit = el.find('div', {"class": "name"}).get_text(strip=True)
                unit_remap = {
                    "מג": "mg",
                    "גרם": "g",
                    "קל": "kg",
                }
                unit = unit_remap.get(unit, unit)
                data['nutrition'][serving].append({
                    "element": el.find('div', {"class": "text"}).get_text(strip=True),
                    "value": el.find('div', {"class": "number"}).get_text(strip=True),
                    "unit": unit,
                })

    warnings = soup.find('li', {"class": "productSymbols"})
    if warnings:
        images = warnings.find_all("img")
        data['warnings'] = [i.get('src') for i in images]
        # data['warnings'] = [i.get('alt') for i in images] # == "red.symbol.classfication.320"
        # 320 => sodium
        # 321 => sugar
        # 322 => fat

    healthier = soup.find('section', {"class": "healthier"})
    if healthier:
        data['healthier'] = [e.get("data-product-code").replace("P_", "") for e in healthier.find_all("div", {"class": "SEARCH"})]

    shufersal_db[barcode] = data
    shufersal_db.commit()
    return data

