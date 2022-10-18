from models import Rig, Blockchain, Currency, Calculator
import provider

"""
Calculator script requires some blockchain network and market data.
Provide values manually by passing required data (examples below),
or use provider class to fetch those values automatically.
"""

# Fetch required data from the APIs
blockchain_params = provider.BlockchainData().get()
currency_params = provider.MarketData().get('PLN')

# Create Currency instance
blockchain = Blockchain(**blockchain_params)

# Create Currency instance
currency = Currency(**currency_params)

# Create Rig instance, provide hashrate in H/s and valid algorithm
rig = Rig(name='Test', hashrate=50_000_000, algorithm='progpow')

# Create Calculator instance
calculator = Calculator(rig=rig, blockchain=blockchain, currency=currency)

print(calculator.get_report())

# ------------------------------------------------

## PROVIDING DATA MANUALLY
# dict with minimum required currency data
currency_params = {
    'symbol': 'USD',  # currency symbol
    'btc_price': 20_000,  # btc price in that currency
    'epic_price': 0.45  # epic price in that currency
    }

# dict with minimum required blockchain data
blockchain_params = {
    'name': "Mainnet",
    'algo': "progpow",
    'height': 1156987,
    'reward': 4,
    'avg_time': 60,
    'network_hashrate': {'cuckoo': 979167, 'progpow': 72947829328, 'randomx': 33265912}
    }