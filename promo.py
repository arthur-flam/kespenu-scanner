from __future__ import annotations
import math
from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional


class Availability(Enum):
    public = 0
    mohadon = 1
    credit_card = 2
    other = 3

class RewardType(Enum):
    NO_PROMOTION = 0
    DISCOUNT_IN_AMOUNT = 1
    DISCOUNT_IN_PERCENTAGE = 2
    DISCOUNT_BY_AMOUNT = 3
    DISCOUNT_WHEN_MINIMUM_PURCHASE_AMOUNT = 4
    DISCOUNT_FOR_MEMBERS = 5
    DISCOUNT_IF_PURCHASING_OTHER_ITEMS = 6
    SECOND_OR_THIRD_INSTANCE_FOR_FREE = 7
    SECOND_WITH_DISCOUNT = 8
    SECOND_WITH_DIFFERENT_DISCOUNT = 9
    MULTIPLE_DISCOUNTED_ITEMS = 10
    OTHER = 11


@dataclass
class Promo:
    promo_id: int
    store_id: int
    description: str
    remark: Optional[str]
    type: RewardType
    discount_rate: Optional[float]  # as reported by the chain
    discount_price: Optional[float] # as reported by the chain
    discount_type: Optional[int]
    min_purchase_amount: Optional[float]
    update_time: datetime
    start_time: datetime
    end_time: datetime
    items: List = field(repr=False)# [PromoItem] PromoItem.(ItemCode|ItemType|IsGiftItem)
    availability: Availability
    min_qty: float
    max_qty: Optional[float]
    min_items_offered: float
    allow_multiple_discounts: bool
    is_weighted: bool
    restrictions: Dict
    availability: List[Availability]
    raw: Dict = field(repr=False)

    # computed on demand given info on regular prices
    price: Optional[float] = None          # computed from the type and discounts
    discount: Optional[float] = None       # computed from the type and discounts


    def compute_discount(self, prices):
        self.price = None
        self.discount = None

        gift_codes = [i['ItemCode'] for i in self.items if i["IsGiftItem"]]
        item_codes = [i['ItemCode'] for i in self.items if not i["IsGiftItem"]]

        gift_prices = [prices[c].price for c in gift_codes if c in prices]
        item_prices = [prices[c].price for c in item_codes if c in prices]

        if not item_prices: # none of the articles seem to be on sale at the moment...
            return

        # it's simpler to compute the before after prices on all that's needed to be bought
        # regular_price = min(item_prices) # we could be pessimistic about what item you want to be
        regular_price = max(item_prices)   # but let's say you want the most expensive of them
        regular_price_basket = regular_price * self.min_qty

        make_it_fail = False
        if self.type.value == RewardType.NO_PROMOTION.value:
            self.price = regular_price

        elif self.type.value == RewardType.DISCOUNT_IN_AMOUNT.value:
            # print("self.min_qty", self.min_qty)
            # self.price = (regular_price_basket - self.discount_price) / self.min_qty
            self.price = self.discount_price / self.min_qty

        elif self.type.value == RewardType.DISCOUNT_IN_PERCENTAGE.value:
            second_at_discount =  "השני ב" in self.description
            self.price = regular_price * (1 - self.discount_rate / (2 if second_at_discount else 1))

        elif self.type.value == RewardType.DISCOUNT_BY_AMOUNT.value:
            self.price = regular_price - self.discount_rate

        elif self.type.value == RewardType.DISCOUNT_WHEN_MINIMUM_PURCHASE_AMOUNT.value:
            self.price = self.discount_price / self.min_qty

        elif self.type.value == RewardType.DISCOUNT_FOR_MEMBERS.value:
            raise NotImplementedError

        elif self.type.value == RewardType.DISCOUNT_IF_PURCHASING_OTHER_ITEMS.value:
            # when there are gifts, the promo price is 0, but we have to buy the other products...
            # TODO: ideally, we should check if there are promos on the products we have to buy!
            discount_price = self.discount_price or 0.0
            discount_price += regular_price_basket
            # print("discount_price", discount_price)
            # print("regular_price_basket", regular_price_basket)
            # print("gift_prices", gift_prices)
            if gift_prices: # maybe gifts are not sold/available so we can't know their prices
                regular_price_basket += max(gift_prices)
            # print("regular_price_basket", regular_price_basket)
            self.price = 0
            self.discount = (regular_price_basket - discount_price) / regular_price_basket
            return
            # make_it_fail=True

        elif self.type.value == RewardType.SECOND_OR_THIRD_INSTANCE_FOR_FREE.value:
            self.price = regular_price * (1 - (1 / self.min_qty))

        elif self.type.value == RewardType.SECOND_WITH_DISCOUNT.value:
            if "השני ב" in self.description:
                self.price = (regular_price + self.discount_price) / 2
            else:
                self.price = self.discount_price / self.min_qty
                make_it_fail = True

        elif self.type.value == RewardType.SECOND_WITH_DIFFERENT_DISCOUNT.value:
            if not self.discount_price:
                self.price = regular_price * (1 - (self.discount_rate / self.min_qty))
            else:
                self.price = (regular_price * (self.min_qty - 1) + self.discount_price) / self.min_qty

        elif self.type.value == RewardType.MULTIPLE_DISCOUNTED_ITEMS.value:
            self.price = self.discount_price / self.min_qty

        elif self.type.value == RewardType.OTHER.value:
            raise NotImplementedError

        elif self.remark and 'מחיר המבצע הינו המחיר לק"ג' in self.remark:
            self.price = self.discount_price

        # elif self.discount_price and self.min_qty: # fallback...
        #     self.price = self.discount_price / self.min_qty

        else:
            raise NotImplementedError

        if self.remark and 'מחיר המבצע הינו המחיר לק"ג' in self.remark:
            self.price = self.discount_price

        self.discount = (regular_price - self.price) / regular_price
        if make_it_fail:
            print(self)
            print("regular_price", regular_price)
            print("regular_price_basket", regular_price_basket)
            # print({**self.raw, "PromotionItems": None})
            print(self.raw)
            print(f"price {self.price}")
            print(f"discount {self.discount}")
            raise NotImplementedError


    @staticmethod
    def compute_discounts(promos: Dict[str, Promo], prices):
        """compute the 'real' discount of all the promotions""" 
        for p in promos.values():
            p.compute_discount(prices)


    @staticmethod
    def from_dict(data):
        # print(data)
        reward_type = RewardType(data['RewardType'])
        if "DiscountRate" in data:
            if reward_type.value == RewardType.DISCOUNT_BY_AMOUNT.value:
                discount_rate = int(data["DiscountRate"]) / 100
            else:
                discount_rate = int(data["DiscountRate"]) * (10 ** - (1 + math.floor(math.log10(data["DiscountRate"]))))
        else:
            discount_rate = None
        return Promo(
            store_id=data['store_id'],
            promo_id=data['PromotionId'],
            discount_price=data.get('DiscountedPrice'),
            discount_rate=discount_rate,
            discount_type=data.get('DiscountType'),
            min_purchase_amount=data.get('MinPurchaseAmnt'),
            description=data['PromotionDescription'],
            remark=data.get('Remark'),
            allow_multiple_discounts=data['AllowMultipleDiscounts'],
            is_weighted=data['IsWeightedPromo'],
            min_qty=data['MinQty'],
            max_qty=data.get('MaxQty'),
            min_items_offered=data['MinNoOfItemOfered'],
            type=reward_type,
            update_time=datetime.strptime(data['PromotionUpdateDate'], "%Y-%m-%d %H:%M"),
            start_time=datetime.strptime(f"{data['PromotionStartDate']} {data['PromotionStartHour']}", "%Y-%m-%d %H:%M"),
            end_time=datetime.strptime(f"{data['PromotionEndDate']} {data['PromotionEndHour']}", "%Y-%m-%d %H:%M"),
            items=data['PromotionItems'],
            availability=[Availability(c) for c in data['Clubs']],
            restrictions=data['AdditionalRestrictions'],
            raw=data,
        )


    def __eq__(self, other):
        return self.id == other.id

    @staticmethod
    def pretty_print(promo: Promo, items=None, prices=None):
        print(promo)
        if items:
            for i in promo.items:
                code = i['ItemCode']
                if i['IsGiftItem']:
                    print("[gift]", end='')
                if prices and code in prices:
                    print(" ", prices[code])
                if items and code in items:
                    print(" ",items[code])
