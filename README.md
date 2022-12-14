# epic-mining-calculator
___
Tools to calculate mining profitability for EPIC - PoW cryptocurrency and blockchain.

More on [epic.tech](https://epic.tech), for developers [docs.epic.tech](https://docs.epic.tech).

___

### File structure:
- models.py - manage data with **pydantic** library
- provider.py - fetch blockchain and market data from 3rd party APIs
- examples.py - examples how to use this script


### How to start:
```bash
git clone https://github.com/epic/mining-calculator
cd mining-calculator
```

```python
# -- examples.py

from models import Rig, Blockchain, Currency, Calculator
import provider

# Fetch required data from the APIs, you can use provider class or manually provide valid dictionary.
blockchain_params = provider.BlockchainData().get()

# Create Blockchain instance
blockchain = Blockchain(**blockchain_params)

# Create Currency instance
usd_details = provider.MarketData().get('USD')
currency = Currency(usd_details)

# Create Rig instance, provide hashrate in H/s and valid algorithm
rig = Rig(name='Test', hashrate=50_000_000, algorithm='progpow')

# Create Calculator instance
calculator = Calculator(rig=rig, blockchain=blockchain, currency=currency)

print(calculator.get_report())
```

Output:
```bash
{
    'rig': {
      'name': 'Test',
      'hashrate': 50000000, 
      'algorithm': 'progpow', 
      'power_consumption': None
        }, 
        
    'epic_per_day': 1.65177764, 
    'blocks_per_day': 0.437, 
    'hours_for_block': 54.9,
    'currency': 'USD',  
    'yield_value': 1.78, 
    'profit': 1.78
    'costs': 0.0, 
    'cost_pool': 0.0, 
    'cost_energy': 0.0, 

}

```
