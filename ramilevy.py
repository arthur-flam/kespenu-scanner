


api_host = "https://www.rami-levy.co.il"
def barcode_metadata(barcode: str, no_cache=False):
    # To investigate: https://www.rami-levy.co.il/he/online/feed?item=3387390525960

    # TODO: to know how to understand the API responses (code > str), we need to fetch
    # curl 'https://api-prod.rami-levy.co.il/api/v2/site/static/menu' -X POST -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjIxNzE5ZDM2NzI0OGYyZDAwY2RkMThmM2U5ZmJhNGYxYTU1OTRkYjZlYjI3ODY4ZTlmZmJhNWI0YTdmNTc2Y2IwNDg3N2FiNjY1ODMwYWNjIn0.eyJhdWQiOiIzIiwianRpIjoiMjE3MTlkMzY3MjQ4ZjJkMDBjZGQxOGYzZTlmYmE0ZjFhNTU5NGRiNmV$' -H 'Locale: he' -H 'Origin: https://www.rami-levy.co.il' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'Content-Length: 0'
    "/api/v2/site/static/menu"

    # TODO: then to get the product data we need:
    # curl 'https://www.rami-levy.co.il/api/items' -X POST -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:102.0) Gecko/20100101 Firefox/102.0' -H 'Accept: application/json, text/plain, */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://www.rami-levy.co.il/he/online/feed?item=3387390525960' -H 'newrelic: eyJ2IjpbMCwxXSwiZCI6eyJ0eSI6IkJyb3dzZXIiLCJhYyI6IjI3NzI1OTUiLCJhcCI6IjkxNDEyOTI1OSIsImlkIjoiMjZjZDgzZjAwMjUyYjAxYiIsInRyIjoiNmE2NTRmMWNlODBiYTFlMDBjNzc1YWJlNTU4YjJhZTAiLCJ0aSI6MTY1NDQzOTUxMzg0Nn19' -H 'traceparent: 00-6a654f1ce80ba1e00c775abe558b2ae0-26cd83f00252b01b-01' -H 'tracestate: 2772595@nr=0-1-2772595-914129259-26cd83f00252b01b----1654439513846' -H 'authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjIxNzE5ZDM2NzI0OGYyZDAwY2RkMThmM2U5ZmJhNGYxYTU1OTRkYjZlYjI3ODY4ZTlmZmJhNWI0YTdmNTc2Y2IwNDg3N2FiNjY1ODMwYWNjIn0.eyJhdWQiOiIzIiwianRpIjoiMjE3MTlkMzY3MjQ4ZjJkMDBjZGQxOGYzZTlmYmE0ZjFhNTU5NGRiNmV$' -H 'Locale: he' -H 'Content-Type: application/json;charset=utf-8' -H 'Origin: https://www.rami-levy.co.il' -H 'Connection: keep-alive' -H 'Cookie: i18n_redirected=he; auth.strategy=local; _gcl_au=1.1.414624053.1654439509; __cf_bm=Ag1Gz7b4maKZj_N6jkHSRjl.mHgj3M3JVws_FAVo7xA-1654439510-0-AaibSe7H8mUzR3Ip4bdQXvOeRozw1lgmHWgmSJGPWDpJsC3me2tja7b6GtgGXLOeDwWM2YkjXjyMeUZ1PrxCQGr4QGq/ihmiO+q0xbPQzkoSS/anxOmt/mfh5I8J1bMVWQ==' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-origin' --data-raw '{"ids":"3387390525960","type":"barcode"}'
    "/api/items"
    # data = r.json['data'][0]

    ### inside data
    # kashrut/kashruts: lots of info...
    # category: "department|group|subGroup".name|id|sort|slug

    # image_url = f"https://img.rami-levy.co.il/product/{barcode}/small.jpg"
    # "images": lists some of small/large/original/trim/transparent

    # "gs"
    #    name": "קראנץ שוקולד 10*500גרם N9",
    #    short_name": "דגני בוקר קראנץ' עם שוקולד 500 גרם",
    #    BrandName": "נסטלה",
    #    Country_of_Origin": "FR",
    #    Ingredient_Sequence_And_Name # 2 lines, 2nd is name
    #    internal_product_description": "קראנץ' 10*500גרם חדש 2016",
    #    Product_Description_English": "CRUNCH Cereal 10x500g N9 IL",

    #    Product_Dimensions

    #    Fat_Percentage_in_Product": null,
    #    Food_Symbol_Red": [{ "code": "FSR3", "value": "סוכר בכמות גבוהה" }],
    #    Diet_Information": [5514, 5513, 5531],
    #    Cream_Percentage_in_Product": null

    #    Serving_Size_Description": "",


    #    Allergen_Type_Code_and_Containment": [6810],
    #    Allergen_Type_Code_and_Containment_May_Contain": [6806, 6807, 6818, 6840],

    #    Fruit_Percentage_in_Product": null,
    #    Healthy_Product": "",
    #    Contains_Sulfur_Dioxide": null,
    #    litzman": false,
    #    pH": null,

    #    Alcohol_Percentage_in_Product": null,
    #    Forbidden_Under_the_Age_of_18": null,
    #    Hazard_Precautionary_Statement": "<br />\n<br />\n<br />\n",

    #    Serving_Suggestion": "",
    #    Consumer_Storage_Instructions": "לשמור במקום קריר ויבש",

    #    Net_Content": { "UOM": "גרם", "text": "500 גרם", "value": "500" },

#         "Nutritional_Values": [
#           {
#             "code": "79001",
#             "label": "אנרגיה (קלוריות)",
#             "fields": [
#               {
#                 "col_code": "78001",
#                 "field_id": "5816",
#                 "col_field_id": "6066",
#                 "UOM": "קלוריות",
#                 "col_label": "ל-100 גרם",
#                 "text": "403 קלוריות",
#                 "value": "403",
#                 "field_name": "Energy_per_100_grams"
#               },






