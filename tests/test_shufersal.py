import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from shufersal import barcode_metadata


products = [
    # ('8801055707010', {
    #     'name': 'nescafe cappuccino classic',
    # }),
    ('3387390525960', {
       'name': 'xxx'
    })
]

### Today we get this:
# {'allergens': 'חלב',
#  'brand': 'נסקפה',
#  'categoryCodes': ['A', 'A13', 'A1305', 'A130504'],
#  'categoryID': 'A130504',
#  'categoryLevel1': 'סופרמרקט',
#  'categoryLevel2': 'משקאות, אלכוהול ויין',
#  'categoryLevel3': 'קפה ותה',
#  'categoryLevel4': 'קפה נמס, שוקו ומלבין ',
#  'description': "נסקפה קפוצ'ינו קלאסי הוא שילוב בין תערובת חלב מפנקת, קפה מבית "
#                 'נסקפה ושכבת קצף אוורירית\n'
#                 '• מיוצר מתערובת פולי קפה שנבחרו בקפידה ונקלו קלות\n'
#                 '• רק מוזגים מים חמים והמשקה מוכן!\n'
#                 '• האריזה מכילה 10 מנות אישיות\n'
#                 '• כל שלב בהפקת קפה זה נעשה תוך הקפדה על קיימות וכבוד לסביבה, '
#                 'לחקלאים ולקהילה',
#  'healthier': ['3903788', '3903771', '8801055706976', '8801055706952'],
#  'images': ['https://res.cloudinary.com/shufersal/image/upload/f_auto,q_auto/v1551800922/prod/product_images/products_zoom/LAH42_Z_P_8801055707010_1.png',
#             'https://res.cloudinary.com/shufersal/image/upload/f_auto,q_auto/v1551800922/prod/product_images/products_small/LAH42_S_P_8801055707010_1.png'],
#  'ingredients': 'אבקת חלב כחוש, שמן צמחי מוקשה, מלטודקסטרין, קפה נמס (15%), '
#                 'לקטוז, סוכר, מייצבים (E331, E452, E340), קזאינט, מלח, חומר '
#                 'מונע גיוש (E5 51), שמן קוקוס.',
#  'kosher_authority': 'OU',
#  'kosher_pessah': 'לא לפסח',
#  'kosher_type': 'חלבי',
#  'name': "נסקפה קפוצ'ינו קלאסיק",
#  'nutrition': {'100 גרם': [{'element': 'סוכרים מתוך פחמימות',
#                             'unit': 'g',
#                             'value': '28.8'},
#                            {'element': 'אנרגיה', 'unit': 'kg', 'value': '497'},
#                            {'element': 'חלבונים', 'unit': 'g', 'value': '13.9'},
#                            {'element': 'פחמימות', 'unit': 'g', 'value': '55.1'},
#                            {'element': 'שומנים', 'unit': 'g', 'value': '24.5'},
#                            {'element': 'כולסטרול', 'unit': 'mg', 'value': '6'},
#                            {'element': 'נתרן', 'unit': 'mg', 'value': '500'},
#                            {'element': 'מתוכם שומן רווי',
#                             'unit': 'g',
#                             'value': '20.9'},
#                            {'element': 'חומצות שומן טרנס',
#                             'unit': 'g',
#                             'value': 'פחות מ 0.5'},
#                            {'element': 'כפיות סוכר',
#                             'unit': '',
#                             'value': '7.25'}],
#                '100 מ"ל מוכן': [{'element': 'סוכרים מתוך פחמימות',
#                                  'unit': 'g',
#                                  'value': '1.7'},
#                                 {'element': 'אנרגיה',
#                                  'unit': 'kg',
#                                  'value': '30'},
#                                 {'element': 'מתוכם שומן רווי',
#                                  'unit': 'g',
#                                  'value': '1.2'},
#                                 {'element': 'חומצות שומן טרנס',
#                                  'unit': 'g',
#                                  'value': 'פחות מ 0.5'}],
#                'מנה': [{'element': 'סוכרים מתוך פחמימות',
#                         'unit': 'g',
#                         'value': '3.6'},
#                        {'element': 'אנרגיה', 'unit': 'kg', 'value': '62'},
#                        {'element': 'חלבונים', 'unit': 'g', 'value': '1.7'},
#                        {'element': 'פחמימות', 'unit': 'g', 'value': '6.9'},
#                        {'element': 'שומנים', 'unit': 'g', 'value': '3.1'},
#                        {'element': 'כולסטרול', 'unit': 'mg', 'value': '0.8'},
#                        {'element': 'נתרן', 'unit': 'mg', 'value': '63'},
#                        {'element': 'מתוכם שומן רווי',
#                         'unit': 'g',
#                         'value': '2.6'},
#                        {'element': 'חומצות שומן טרנס',
#                         'unit': 'g',
#                         'value': 'פחות מ 0.5'},
#                        {'element': 'כפיות סוכר', 'unit': '', 'value': '1'}]},
#  'producer_country': 'דרום קוריאה',
#  'producer_name': 'נסקפה',
#  'אבקת חלב נוכרי': 'לא'}


class TestShufersalMetadata(unittest.TestCase):
  def test_is_int(self):
    barcode, nescafe_data = products[0]
    data = barcode_metadata(barcode, no_cache=True)
    from pprint import pprint
    pprint(data)
    # self.assertEqual(bool(is_int("4")), True)



if __name__ == '__main__':
  unittest.main()
