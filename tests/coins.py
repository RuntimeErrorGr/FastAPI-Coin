from app.schemas.coin import CoinRead

BTC = CoinRead(symbol="btc", coingecko_id="bitcoin", name="Bitcoin")
ETH = CoinRead(symbol="eth", coingecko_id="ethereum", name="Ethereum")
USD = CoinRead(symbol="usd", coingecko_id="usd", name="US Dollar")
XRP = CoinRead(symbol="xrp", coingecko_id="ripple", name="XRP")

COINS = {coin.symbol: coin for coin in (BTC, ETH, USD, XRP)}
