"""
Format reference:
https://www.nevo.co.il/law_html/law01/501_131.htm


Availability should be "at least 99.5%", so obviously we get shitty latency, at least 7min of downtime a day, and tons of failed requests...
"""
import io
import gzip
from enum import Enum
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional

import httpx
from bs4 import BeautifulSoup
from bs4.element import Tag


@dataclass
class Item:
    """
    An item that could be in stock somewhere...
    The data should be the same accross chains. 
    """
    barcode: str
    # barcode_type: int # 0: internal barcode, 1: barcode embedded on the prodcut
    # We don't care about querying most of the fields, so it's possible we should just JSON all the fields below...
    name: str

    unit: str
    unit_of_measure: str # according to rules from 1991
    is_weighted: bool
    quantity: float
    quantity_in_package: float

    manufacturer_name: str # if imported should have the importer's name...
    manufacturer_country: str # everything according to israeli rule 1145 
    manufacturer_description: str

    @staticmethod
    def from_dict(data):
        return Item(
            barcode = data['ItemCode'],
            # barcode_type = data['ProductType'],
            name = data['ItemName'],
            manufacturer_name = data['ManufacturerName'],
            manufacturer_country = data['ManufactureCountry'],
            manufacturer_description = data['ManufacturerItemDescription'],
            unit = data['UnitQty'],                   # FIXME: normalize spellings with utility function...
            unit_of_measure = data['UnitOfMeasure'],  # FIXME: normalize spellings with utility function...
            quantity = data['Quantity'],
            quantity_in_package = data['QtyInPackage'],
            is_weighted = data['bIsWeighted'],
        )



@dataclass
class Price:
    """Price of a product at a given time"""
    # TODO: create a materialized view with the most current prices
    #       for each product, in each chain+store
    barcode: str
    update_time: datetime
    price: float
    price_per_unit_of_measure: float
    allow_discount: bool
    store_id: int # foreign key
    # status: int # 0: removed from sale, 1: updated price, 2: new product
    # chain_id: int # foreign key (not needed?)

    @staticmethod
    def from_dict(data):
        return Price(
            barcode = data['ItemCode'],
            store_id = data['store_id'],
            update_time = datetime.strptime(data['PriceUpdateDate'], "%Y-%m-%d %H:%M"),
            price = data['ItemPrice'],
            price_per_unit_of_measure = data['UnitOfMeasurePrice'],
            allow_discount = data['AllowDiscount'],
            # status = data['Status'],
        )





class DataFileType(Enum):
    """
    Different data files available for download from chains. The 'All' versions have all data vs changes otherwise.
    According to the law, the non-all version should have hourly updates, as well as product removals.
    """
    All, Prices, PricesFull, Promos, PromosFull, Stores = range(6)



class StoreType(Enum):
    Unknown = None
    Physical = 1
    Online = 2
    Mixed = 3

@dataclass
class Store:
    store_id: int

    name: str
    address: str
    city: str
    zipcode: str

    subchain_id: int
    subchain: str
    chain_id: int    # foreign key

    update_time: datetime
    bikoret: Optional[int] # what is this?
    type: StoreType

    lon: Optional[float] = None
    lat: Optional[float] = None

    @staticmethod
    def from_dict(data):
        # print(data['CHAINNAME'])
        return Store(
            store_id=data['STOREID'],
            subchain=data['SUBCHAINNAME'],
            subchain_id=data['SUBCHAINID'],
            chain_id=data['chain_id'],
            name=data['STORENAME'],
            address=data['ADDRESS'],
            city=data['CITY'],
            zipcode=data['ZIPCODE'],
            update_time=data['update_time'],
            bikoret=data['BIKORETNO'],
            type=StoreType(data['STORETYPE']),
        )

    @staticmethod
    def is_valid(store_id: int):
        return store_id >= 0


def url_reader(url, debug_cache=False) -> str:
    """Download and return the text content of data file URLs"""
    from pathlib import Path
    cache_path = Path('test.txt')
    if debug_cache and cache_path.exists():
        print("[cached]")
        with open('test.txt') as f:
            return f.read()
    r = httpx.get(url)
    with gzip.open(io.BytesIO(r.content)) as f:
        data = f.read().decode(
            'utf-8-sig',  # starts with a BOM
            "ignore",
        )
    if debug_cache:
        with cache_path.open('w') as f:
            f.write(data)
    return data


@dataclass
class Chain:
    chain_id: int
    name: str
    label: str
    data: Dict    # e.g data on how to read the XML data files

    # Now we describe how to actually download price/promo data for each chain
    # The data files are XML files, each chain using a slightly different convention
    # Here are decent defaults, which chains might override with Chain.data...
    item_tag_name = 'Item'
    promotion_tag_name = 'Promotion'
    promotion_update_tag_name = 'PromotionUpdateDate'
    date_format = '%Y-%m-%d'
    date_hour_format = '%Y-%m-%d %H:%M'
    update_date_format = '%Y-%m-%d %H:%M'


    def store_url(self, store_id: int, type: DataFileType) -> str:
        """Returns a url with data for the given store."""
        if self.name == "shufersal":
            from shufersal import store_url as shuferal_store_url
            return shuferal_store_url(store_id, type)
        else:
            raise NotImplementedError

    def fetch_stores_info(self):
        stores_file_url = self.store_url(None, DataFileType.Stores)
        # stores_file_url = None
        stores_data = url_reader(stores_file_url, debug_cache=False)
        soup = BeautifulSoup(stores_data, 'lxml-xml')
        self.chain_id = int(soup.find("CHAINID").get_text())
        update_time = datetime.strptime(soup.find("LASTUPDATEDATE").get_text(), self.date_format)
        stores = {}
        for store_e in soup.find("STORES").find_all("STORE"):
            store = {"chain_id": self.chain_id, "update_time": update_time}
            for attr in store_e.children:
                store[attr.name] = attr.get_text()
                if attr.name in int_attrs:
                    try:
                        store[attr.name] = int(store[attr.name])
                    except:
                        if not store[attr.name]:
                            store[attr.name] = None
                        else:
                            raise ValueError((store, attr.name))
            stores[store['STOREID']] = Store.from_dict(store)
            self.label = store['CHAINNAME']
        return stores

    def tag_itemprices(self, tag: Tag, store_id: int):
        items = {}
        prices = {}
        # tweaks in https://github.com/korenLazar/supermarket-scraping/blob/master/supermarket_chain.py#L123
        for item_e in tag.find("Items").find_all("Item"):
            item = {"store_id": store_id}
            for attr in item_e.find_all():
                item[attr.name] = attr.get_text()
                if attr.name in num_attrs:
                    item[attr.name] = float(item[attr.name])
                elif attr.name in bool_attrs:
                    item[attr.name] = to_bool(item[attr.name])
            items[item['ItemCode']] = Item.from_dict(item)
            prices[item['ItemCode']] = Price.from_dict(item)
        return items, prices

    def tag_promos(self, tag: Tag, store_id: int):
        from promo import Promo
        promos = {}
        for promo_e in tag.find("Promotions").find_all("Promotion"):
            promo = {"store_id": store_id}
            for attr in promo_e.find_all(recursive=False):
                if attr.name not in ("PromotionItems", "AdditionalRestrictions", "Clubs"):
                    promo[attr.name] = attr.get_text()
                    if attr.name in num_attrs:
                        promo[attr.name] = float(promo[attr.name])
                    elif attr.name in int_attrs:
                        promo[attr.name] = int(promo[attr.name])
                    elif attr.name in bool_attrs:
                        promo[attr.name] = to_bool(promo[attr.name])

                if attr.name == "PromotionItems":
                    promo["PromotionItems"] = []
                    for item in attr.find_all("Item"):
                        promo["PromotionItems"].append({
                            "ItemCode": item.ItemCode.get_text(),
                            "ItemType": item.ItemType.get_text(),
                            "IsGiftItem": to_bool(item.IsGiftItem.get_text()),
                        })
                if attr.name == "AdditionalRestrictions":
                    promo["AdditionalRestrictions"] = {}
                    for r_attr in attr.find_all(recursive=False):
                        promo["AdditionalRestrictions"][r_attr.name] = r_attr.get_text()
                        if r_attr.name in bool_attrs:
                            promo["AdditionalRestrictions"][r_attr.name] = to_bool(promo["AdditionalRestrictions"][r_attr.name])
                        elif r_attr.name in num_attrs:
                            promo["AdditionalRestrictions"][r_attr.name] = float(promo["AdditionalRestrictions"][r_attr.name])
                if attr.name == "Clubs":
                    promo["Clubs"] = [int(e.get_text()) for e in attr.find_all("ClubId")]
            promos[promo['PromotionId']] = Promo.from_dict(promo)
        return promos


    def fetch_store_info(self, store_id: int, type: DataFileType):
        store_file_url = self.store_url(store_id, type)
        # store_file_url = None
        store_data = url_reader(store_file_url, debug_cache=False)
        soup = BeautifulSoup(store_data, 'lxml-xml')
        if type.value in (DataFileType.All.value, DataFileType.Prices.value, DataFileType.PricesFull.value):
            return self.tag_itemprices(soup, store_id)
        elif type.value in (DataFileType.Promos.value, DataFileType.PromosFull.value):
            return self.tag_promos(soup, store_id)
        else:
            raise ValueError(type)



bool_attrs = (
    # prices
    "bIsWeighted", "AllowDiscount",
    # ItemStatus always '1'
    # promos
   "AllowMultipleDiscounts", "IsWeightedPromo",
    # promos.PromotionItems
    "IsGiftItem",
    # promos.AdditionalRestrictions
    "AdditionalIsCoupon", "AdditionalIsTotal", "AdditionalIsActive",
)
def to_bool(v: str):
    if v == '0': return False
    if v == '1': return True
    raise ValueError(v)

num_attrs = (
    # stores
    "SUBCHAINID", "SUBCHAINID", "BIKORETNO", "CHAINID",
    # prices
    "Quantity", "QtyInPackage", "ItemPrice", "UnitOfMeasurePrice", 'Quantity',
    # promos
    "MinQty", "MaxQty", "DiscountedPrice", "MinNoOfItemOfered", "DiscountRate", "AdditionalGiftCount",
)
int_attrs = (
    "STOREID", "SUBCHAINID", "SUBCHAINID", "BIKORETNO", "CHAINID",
    "PromotionId", "RewardType", "DiscountType", "STORETYPE",
)
