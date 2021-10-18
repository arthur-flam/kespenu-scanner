"""
Access openfoodfacts data

To know more about products, we can check the openfoodfacts database!
Unfortunately (or fortunately!) there is a lot of data...!
to get the data either:
  GUI:     https://world.openfoodfacts.org/cgi/search.pl
  API:     https://world.openfoodfacts.org/api/v0/product/[barcode].json
           https://world.openfoodfacts.org/api/v0/product/737628064502.json
  python:  https://github.com/openfoodfacts/openfoodfacts-python
  DB:      wget -k https://static.openfoodfacts.org/data/openfoodfacts-products.jsonl.gz
           gunzip openfoodfacts-products.jsonl.gz
           !23G... each line is a product
"""
import json
from db import make_db


db_path = './openfoodfacts.sqlite'
dump_jsonl_path='openfoodfacts-products.jsonl'




def init_openfoodfacts(db_path: str = db_path, dump_jsonl_path: str = dump_jsonl_path):
    """Load a data dump to build a local database"""
    db = make_db(db_path)
    with open(dump_jsonl_path) as f:
        idx = 0
        while line := f.readline():
            idx +=1 
            if idx % 10_000 == 0:
                print(f"{idx/1_963_935:.02%}")
                db.commit()
            product = json.loads(line)
            if 'code' in product:
                product_id = product['code']
            elif 'id' in product:
                product_id = product['id']
            else:
                continue
            db[product_id] = line
        db.commit()
    return db


db = make_db(db_path)
# init_openfoodfacts()