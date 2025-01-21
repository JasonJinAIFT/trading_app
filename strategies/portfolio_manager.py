import pandas as pd

class Order:
    def __init__(self,ticker:str,order_type:str,order_direction:str,price:float,quantity:int,):
        self.ticker = ticker
        self.order_type = order_type
        self.order_direction = order_direction
        self.order_price = price
        self.quantity = quantity


class PortfolioManager:
    def __init__(self, initial_cash:float=1000000):
        self.long_positions = {}
        self.short_positions = {}
        self.positions = pd.DataFrame(columns = ['ticker','quantity'])
        self.cash = initial_cash
        self.order_history = []


    def place_order(self, order_detail:Order):
        ticker = order_detail.ticker
        direction = order_detail.order_direction
        quantity = order_detail.quantity
        order_price = order_detail.price

        if quantity==0:
            msg = "订单数量不能为0"
            return msg
        
        if direction == "buy":
            multiplier = 1
        else:
            multiplier = -1

        cost = multiplier * quantity * order_price
        if direction=="buy" and self.cash < cost:
            msg = "现金不足无法买入"
            return msg

        if ticker in self.positions['ticker'].values:
            # 如果已经有持仓了，则直接在原来的row上更改数值
            index = self.positions[self.positions['ticker'] == ticker].index[0]
            self.positions.loc[index, 'quantity'] += quantity*multiplier

            if self.positions.loc[index, 'quantity'] == 0:
                # 如果该操作是平仓，则将这个row删掉
                self.positions = self.positions.drop(index)
        else:
            # 如果是新开的仓位，则新增一个row
            new_position = pd.DataFrame({'ticker': [ticker], 'quantity': [quantity*multiplier]})
            self.positions = pd.concat([self.positions, new_position], ignore_index=True)

        self.order_history.append(order_detail)
        msg = f"Placed a {order_detail.order_type} {order_detail.order_direction} order for {order_detail.num_shares} shares of {ticker} at price {order_detail.order_price}"
        return msg


    def get_portfolio_value(self, prices:dict):
        """
        展示portfolio的总资产，包括现金。
        :param prices: 由于价格一直在变动，所以在请求该函数时提供现时价格以计算组合的总额
        """
        portfolio_value = 0
        unavailable_prices = []
        for _, row in self.positions.iterrows():
            ticker = row['ticker']
            quantity = row['quantity']
            if ticker in prices:
                portfolio_value += quantity * prices[ticker]
            else:
                unavailable_prices.append(ticker)
                print(f"无法获取持仓中的{ticker}价格")

        total_asset = portfolio_value+self.cash

        msg = f"""
        总资产为：{total_asset}
        组合总值为：{portfolio_value}
        现金金额为：{self.cash}, 占比为：{round(self.cash/total_asset,3)*100}%"""
        
        return msg


    def get_positions(self,):
        return self.positions


    def get_order_history(self):
        return self.order_history