"""
Serves data about barcodes.
"""
import os
import pickle
from enum import Enum
from typing import Optional, Dict

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

app = FastAPI()


class DataSource(Enum):
    prices = "prices"
    openfoodfact = "openfoodfact"
    kaspenu = "kaspenu"

class PriceSource(Enum):
    shufersal = "shufersal"



from models import Chain, DataFileType
from promo import Promo
from shufersal import barcode_metadata
from openfoodfacts import db as openfoodfacts_db

shufersal = Chain(
    chain_id=7290027600007,
    name="shufersal",
    label="",
    data={},
)

if not os.path.isfile('prices.pickle'):
    items, prices = shufersal.fetch_store_info(183, type=DataFileType.PricesFull)
    promos = shufersal.fetch_store_info(183, type=DataFileType.PromosFull)
    Promo.compute_discounts(promos, prices)
    with open('prices.pickle', 'wb') as f:
        pickle.dump(
            {"items": items, "prices": prices, "promos": promos},
            f,
            pickle.HIGHEST_PROTOCOL,
        )
else:
    with open('prices.pickle', 'rb') as f:
        data = pickle.load(f)
        items = data['items']
        prices = data['prices']
        promos = data['promos']

promos_for_item = {}
for promo in promos.values():
    for i in promo.items:
        barcode = i['ItemCode']
        if barcode not in promos_for_item:
            promos_for_item[barcode] = set()
        promos_for_item[barcode].add(promo.promo_id)


@app.get("/api/v1/barcode/{barcode_id}")
def get_barcode(barcode_id: str):
    """Returns all the data we have about a given barcode"""
    data = {"barcode_id": barcode_id}
    if barcode_id in openfoodfacts_db:
        data['openfoodfacts'] = openfoodfacts_db[barcode_id]
    # return BarcodeData(**{
    item_promos = [promos[id] for id in promos_for_item.get(barcode_id, [])]
    return jsonable_encoder({
        **data,
        "item": items.get(barcode_id),
        "meta": {
            "shufersal": barcode_metadata(barcode_id)
        },
        "prices": {
            "shufersal": prices.get(barcode_id),
        },
        "promos": {
            "shufersal": item_promos,
        },
        "kaspenu": None,
    })
    # })




@app.get("/api/v1/barcode/{barcode_id}/{database}")
def get_barcode_data(barcode_id: str, datasource: DataSource, store_id: Optional[str] = None):
    """Returns data from a specific data source about a given barcode"""
    if datasource == DataSource.prices:
        # TODO: query db, select where store_id=...
        return {"prices": {}}
    return {}


# https://fastapi.tiangolo.com/tutorial/response-model/
# .get(..., response_model=BarcodeData
# class BarcodeData(BaseModel):
#     barcode_id: str
#     # prices: Dict

@app.get("/api/v1/stores/{chain}")
def get_stores(chain: str, lon: Optional[float] = None, lat: Optional[float] = None, limit: Optional[float] = None):
    """Returns a list of stores near the coordinates"""
    return []
