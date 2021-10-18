# Product Scanner
Prices from all retail chains in Israel [are public](www.gov.il/he/Departments/legalInfo/cpfta_prices_regulations). One can finds hints about the format [here](https://www.nevo.co.il/law_html/law01/501_131.htm). **Let's try to do something with this data!**

## Project Status
> **POC:** it works _just_ well enough for an end-to-end demo. [Click to see a video](https://youtube.com/shorts/M2fvLbaYfqc?feature=share
):


[![Kespenu Scanner Demo](https://img.youtube.com/vi/M2fvLbaYfqc/0.jpg)](http://www.youtube.com/watch?v=M2fvLbaYfqc)



Scan a product barcode from the web application to see:
- Price/promotions (at the Shufersal next to where I live...) 
- Ingredients, allergens, food quality warnings (data from Shufersal)
- [openfoodfacts](https://world.openfoodfacts.org/) info if available

## Dependencies
- `nodejs`
- `python3.8`
- `pip install -r requirements.txt` (ideally use `virtualenv`...). When you update packages edit `requirments.in` and call `pip-compile requirements.in`.

## Run
To start the app:

```bash
npm install
npm run dev
#=> listenning on port 3000

```

> [Click here](https://developer.mozilla.org/en-US/docs/Web/API/Barcode_Detection_API/ean-13.png) to display a test barcode. See the notes below for tips on how to access the app from a mobile device.

To start the backend:

```bash
cd prices
uvicorn server:app --reload
#=> 127.0.0.0:8000/barcode/0123456789
# Docs:
#=> 127.0.0.0:8000/docs
#=> 127.0.0.0:8000/redoc
#=> 127.0.0.0:8000/openapi.json
```

## TODO
### TODO Backend
- [x] fetch prices shufersal
- [x] model to work nicely with all this data
- [x] find best promotions
- [x] openfoodfacts: fetch db, use it
- [x] shufersal: images, descriptions
- [ ] save prices in a database, query it. makes sense to have a materialized view of "current prices"..?
- [ ] crawl all shufersal images and metadata (save html somewhere, then process..)
- [ ] setup daily crawl (for 1 store for now...)

### TODO Frontend
- [x] scan barcode
    * **browser webAPI** - but we need a polyfill for wide support...   
    * scandit.com / dynamysoft work great but commercial
    * best (almost only?) open-source project: quaggaJS

```
    https://serratus.github.io/quaggaJS/
    https://github.com/ericblade/quagga2 (https://github.com/ericblade/quagga2/commits/master/src)
    https://morioh.com/p/1963935c62db
    https://github.com/ericblade/quagga2-react-example
```

- [x] query backend
- [x] display results
- [ ] native?

### TODO Next
- [ ] fetch prices of more retail chains and stores
- [ ] price distribution: histogram per product, show products with most variance, correlated high prices vs average...
- [ ] geolocation, choose store, show map...
- [ ] save prices over time, see them

## Other projects using the open price data
In python:
- [korenLazar/supermarket-scraping](https://github.com/korenLazar/supermarket-scraping) has [tons of scrappers](https://github.com/korenLazar/supermarket-scraping/blob/8a726ff605759beab0f19baaa6d0a926ae2fdf4d/chains/) and understood what the [promos mean](https://github.com/korenLazar/supermarket-scraping/blob/8a726ff605759beab0f19baaa6d0a926ae2fdf4d/promotion.py)

- [beyond-io/superx](https://github.com/beyond-io/superx) with
  * a DB ([schema](https://github.com/beyond-io/superx/blob/bf81c98cb1541c25e16b6800b09ba8fa8c63b968/superx/models/__init__.py))
  * [mappings](https://github.com/beyond-io/superx/blob/bf81c98cb1541c25e16b6800b09ba8fa8c63b968/superx/app.py) of misc attr names between chains
  * [`def standardize_weight_name(self, unit_in_hebrew)`](https://github.com/beyond-io/superx/blob/bf81c98cb1541c25e16b6800b09ba8fa8c63b968/superx/information_extractors/item_info_extractor.py#L245)
- [elikochva/openprices](https://github.com/elikochva/openprices), not much, just with [all scrapers](https://github.com/elikochva/openprices/blob/46cb7d3c085b4ce363d0d0026b88b6b69c57ff70/backend/web_scraper.py), and:
  * https://github.com/elikochva/openprices/blob/46cb7d3c085b4ce363d0d0026b88b6b69c57ff70/backend/sql_interface.py
- [kimi-codes/PriceScan](https://github.com/kimi-codes/PriceScan), mysql ([schema](https://github.com/kimi-codes/PriceScan/blob/8447b4a7babac02f032f664c2af616a71dc12b99/db/init/init.sql)), compose
- [another scrapper](https://github.com/akariv/kan-data-analysis), 


Notable:
- [imrigp/SuperPrice](https://github.com/imrigp/SuperPrice), pretty nice, working API, with a maintained demo online, search...
  * [db schema](https://github.com/imrigp/SuperPrice/blob/82df5d1c20866e67d37db61c5c31231be07b26df/super-price-api/src/main/java/database/Database.java)
- [ganoti/prices](https://github.com/ganoti/prices) in java, with complete crawlers
- [yonicd/supermarketprices](https://github.com/yonicd/supermarketprices) with baskets to price including gas - in R.



## Debugging on mobile device
To do it:
- Make sure your dev server is visible from your mobile
  on windows make sure your network is defined as a "private" network
  if you use VSCode remote debugging and forward ports from your laptop to your server,
    you'll need settings>forward>localPortHost>allInterfaces
  a quick test is pinging your laptop from your mobile...
- then, the main issue is that we use feature only available in "secure contexts"
  to make it work, there are multiple options:
  1. disable checking for this..... for instance in chrome:
     https://stackoverflow.com/questions/34878749/in-androids-google-chrome-how-to-set-unsafely-treat-insecure-origin-as-secure
  2. connect via USB and forward localhost:3000 to your laptop.
       to do this, setup dev mode on your device, install adb, and call
       adb reverse tcp:3000 tcp:3000
  3. Get a self-signed certificate for your dev server (google "nextjs ssl dev"...)
  4. You can play with DNS to have dev.localhost resolve to your laptop's IP:
     A. On your device, try to edit /system/etc/hosts - but it is hard without a rooted phone....
     B. fallback to apps that create a fake VPN, local, that manipulates DNS queries...
        [personalDNSfilter](https://www.zenz-solutions.de/help/)
        but somehow *.localhost (only!) queries are not always (????) resolved by the app,
        so we're out of luck??
