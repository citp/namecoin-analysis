from decimal import Decimal

class Listing():
    def __init__(self, domain, prices, date_seen):
        self.domain = domain
        self.date_seen = date_seen
        for coin_name, price in prices.items():
            if price.find("-") < 0:
                price = Decimal(price)
            else:
                price = None
            setattr(self, coin_name, price)

    def __repr__(self):
    	return "({}, {})".format(self.domain, self.date_seen)

        
