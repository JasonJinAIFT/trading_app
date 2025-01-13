class Order:
    def __init__(self,ticker:str,order_type:str,order_direction:str,price:float,num_shares:int,):
        self.ticker = ticker
        self.order_type = order_type
        self.order_direction = order_direction
        self.order_price = price
        self.num_shares = num_shares


class PortfolioManager:
    def __init__(self, initial_cash:float=1000000):
        self.long_positions = {}
        self.short_positions = {}
        self.cash = initial_cash


    def place_order(self, order_detail:Order):
        ticker = order_detail.ticker
        direction = order_detail.order_direction

        if direction == "buy":
            ticker_position = self.long_positions.get(ticker,[])
            multiplier = 1
        elif direction == "sell":
            ticker_position = self.short_positions.get(ticker,[])
            multiplier = -1

        ticker_position.append(order_detail)
        remaining_cash = self.cash - order_detail.order_price*order_detail.num_shares*multiplier
        self.cash = remaining_cash
        return f"Placed a {order_detail.order_type} {order_detail.order_direction} order for {order_detail.num_shares} shares of {ticker} at price {order_detail.order_price}"

