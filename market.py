import random
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np

class Cryptocurrency:
    def __init__(self, name: str, initial_price: float, initial_volatility: float):
        self.name = name
        self.price = initial_price
        self.volatility = initial_volatility
        self.last_sentiment=0.0
        self.volume = 0
        self.order_book = {"buy": {}, "sell": {}}
        self.price_history = [initial_price]


    def update_price(self,market_sentiment, trades: List[float]):
        # Actualiza el precio basado en el sentimiento del mercado, las operaciones y la volatilidad
        self.last_sentiment=market_sentiment
        price_change = np.random.normal(0, self.volatility)
        trade_impact = sum(trades) * 0.1
        sentiment_impact = market_sentiment * 0.1
        self.price += price_change + trade_impact + sentiment_impact
        self.price = max(0.01, self.price)  # Evita precios negativos
        self.price_history.append(self.price)
        if len(self.price_history) > 100:
            self.price_history.pop(0)
        self.update_volatility()

    def update_volatility(self):
        # Actualiza la volatilidad basada en el historial de precios reciente
        if len(self.price_history) > 1:
            returns = np.diff(np.log(self.price_history))
            self.volatility = np.std(returns) * np.sqrt(len(returns))
        self.volatility = max(0.001, min(0.5, self.volatility))  # Limita la volatilidad entre 0.1% y 50%

    def update_volume(self, new_volume: float):
        # Actualiza el volumen de transacciones
        self.volume += new_volume
        print(self.volume )

    def add_order(self, order_type: str, price: float, amount: float):
        # Agrega una nueva orden al libro de órdenes
        if price not in self.order_book[order_type]:
            self.order_book[order_type][price] = 0
        self.order_book[order_type][price] += amount

    def remove_order(self, order_type: str, price: float, amount: float):
        # Elimina una orden del libro de órdenes
        self.order_book[order_type][price] -= amount
        if self.order_book[order_type][price] <= 0:
            del self.order_book[order_type][price]

class Market:
    def __init__(self, cryptocurrencies: List[Cryptocurrency]):
        # Inicializa el mercado con una lista de criptomonedas
        self.cryptocurrencies = {crypto.name: crypto for crypto in cryptocurrencies}
        self.data = {crypto: crypto for crypto in cryptocurrencies}
        self.timestamp = datetime.now()

    def update(self,sentiment_history):
        # Actualiza el estado del mercado
        print(f"Actualizando el mercado en {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
        self.timestamp += timedelta(minutes=1)
        for crypto in self.cryptocurrencies.values():
            trades = self.match_orders(crypto)
            print(f"Trades en {crypto.name}: {trades}")
            crypto.update_price(sentiment_history[crypto.name][-1],trades)
            crypto.update_volume(sum(abs(trade) for trade in trades))

    def match_orders(self, crypto: Cryptocurrency) -> List[float]:
        # Realiza el emparejamiento de órdenes de compra y venta
        trades = []
        buy_prices = sorted(crypto.order_book["buy"].keys(), reverse=True)
        sell_prices = sorted(crypto.order_book["sell"].keys())

        while buy_prices and sell_prices and buy_prices[0] >= sell_prices[0]:
            buy_price, sell_price = buy_prices[0], sell_prices[0]
            amount = min(crypto.order_book["buy"][buy_price], crypto.order_book["sell"][sell_price])
            trades.append(amount)
            crypto.remove_order("buy", buy_price, amount)
            crypto.remove_order("sell", sell_price, amount)
            if not crypto.order_book["buy"].get(buy_price):
                buy_prices.pop(0)
            if not crypto.order_book["sell"].get(sell_price):
                sell_prices.pop(0)

        return trades