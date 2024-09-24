import random
from datetime import datetime, timedelta
from typing import List, Dict
import numpy as np

class Cryptocurrency:
    def __init__(self, name: str, initial_price: float, initial_volatility: float):
        self.name = name
        self.price = initial_price
        self.initial_price = initial_price  # Almacenar el precio inicial para mean reversion
        self.volatility = initial_volatility  # Expresada como desviación estándar porcentual (e.g., 10.0 para 10%)
        self.last_sentiment = 0.0
        self.volume = 0
        self.order_book = {"buy": {}, "sell": {}}
        self.price_history = [initial_price]

    def update_price(self, market_sentiment, trades: List[float]):
        """
        Actualiza el precio basado en el sentimiento del mercado, las operaciones y la volatilidad.
        Implementa límites para evitar cambios de precios extremos y añade reversión a la media.
        """
        self.last_sentiment = market_sentiment

        # Cambio de precio aleatorio basado en volatilidad
        price_change_percentage = np.random.normal(0, self.volatility / 100)
        price_change_percentage = np.clip(price_change_percentage, -0.02, 0.02)  # Limitar a +/-2%
        price_change = self.price * price_change_percentage

        # Impacto de las operaciones
        trade_impact_percentage = sum(trades) * 0.005  # Multiplicador reducido a 0.5%
        trade_impact_percentage = np.clip(trade_impact_percentage, -0.02, 0.02)  # Limitar a +/-2%

        # Impacto del sentimiento del mercado
        sentiment_impact_percentage = market_sentiment * 0.005  # Multiplicador reducido a 0.5%
        sentiment_impact_percentage = np.clip(sentiment_impact_percentage, -0.02, 0.02)  # Limitar a +/-2%

        # Reversión a la media hacia el precio inicial
        mean_reversion_strength = 0.01  # Fuerza de reversión a la media (ajustable)
        mean_reversion = (self.initial_price - self.price) * mean_reversion_strength

        # Actualizar el precio
        self.price += self.price * (price_change_percentage + trade_impact_percentage + sentiment_impact_percentage) + mean_reversion
        self.price = max(0.01, self.price)  # Evita precios negativos
        self.price_history.append(self.price)

        if len(self.price_history) > 100:
            self.price_history.pop(0)

        self.update_volatility(trades)

        # Depuración
        # print(f"{self.name} - Precio actualizado: {self.price:.2f}, Volatilidad: {self.volatility:.2f}%")

    def update_volatility(self, trades: List[float]):
        """
        Actualiza la volatilidad basada en el historial de precios reciente y la actividad de trading.
        Reduce la volatilidad a medida que aumenta la estabilidad (más operaciones).
        """
        if len(self.price_history) > 1:
            returns = np.diff(np.log(self.price_history))
            new_volatility = np.std(returns) * np.sqrt(len(returns)) * 100  # Convertir a porcentaje

            # Ajustar la volatilidad:
            # - Más operaciones (mayor volumen) => menor volatilidad
            # - Menos operaciones => mayor volatilidad
            trade_volume = sum(abs(trade) for trade in trades)
            adjustment_factor = 1 / (1 + trade_volume / 1000)  # Ajustar según el volumen de operaciones

            # Actualizar volatilidad con ajuste basado en operaciones
            adjusted_volatility = new_volatility * adjustment_factor

            # Limitar la volatilidad dentro de rangos realistas
            if self.price > 1000:
                self.volatility = max(0.1, min(5.0, adjusted_volatility * 0.9))
            elif self.price > 100:
                self.volatility = max(0.1, min(10.0, adjusted_volatility * 0.95))
            else:
                self.volatility = max(0.1, min(20.0, adjusted_volatility))

            # Depuración
            # print(f"{self.name} - Nueva volatilidad: {self.volatility:.2f}%")
        else:
            # Mantener la volatilidad inicial si no hay suficientes datos
            pass

    def update_volume(self, new_volume: float):
        """
        Actualiza el volumen de transacciones.
        """
        self.volume += new_volume
        # print(f"Volumen de {self.name}: {self.volume}")

    def add_order(self, order_type: str, price: float, amount: float):
        """
        Agrega una nueva orden al libro de órdenes.
        """
        if price not in self.order_book[order_type]:
            self.order_book[order_type][price] = 0
        self.order_book[order_type][price] += amount

    def remove_order(self, order_type: str, price: float, amount: float):
        """
        Elimina una orden del libro de órdenes.
        """
        self.order_book[order_type][price] -= amount
        if self.order_book[order_type][price] <= 0:
            del self.order_book[order_type][price]

class Market:
    def __init__(self, initial_prices: Dict[str, float], initial_volatilities: Dict[str, float]):
        """
        Inicializa el mercado con una lista de criptomonedas usando los precios y volatilidades iniciales proporcionados.
        """
        self.cryptocurrencies = {
            name: Cryptocurrency(name, price, initial_volatility)
            for name, price, initial_volatility in zip(initial_prices.keys(), initial_prices.values(), initial_volatilities.values())
        }
        self.timestamp = datetime.now()

    def update(self, sentiment_history):
        """
        Actualiza el estado del mercado.
        """
        # print(f"Actualizando el mercado en {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}...")
        self.timestamp += timedelta(minutes=1)
        for crypto in self.cryptocurrencies.values():
            trades = self.match_orders(crypto)
            # print(f"Trades en {crypto.name}: {trades}")
            sentiment = sentiment_history.get(crypto.name, [0.0])[-1]
            crypto.update_price(sentiment, trades)
            crypto.update_volume(sum(abs(trade) for trade in trades))

    def match_orders(self, crypto: Cryptocurrency) -> List[float]:
        """
        Realiza el emparejamiento de órdenes de compra y venta.
        """
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
