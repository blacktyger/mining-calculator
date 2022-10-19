"""
Models to store and process data using 'pydantic' library.
"""

import re
from datetime import datetime as dtime

from pydantic import BaseModel, Field, validator

DECIMAL = 10 ** 8
HALVINGS = [1157760, 1224000, 2275200]
BLOCK_TIME = 60
ALGORITHMS = ['cuckoo', 'progpow', 'randomx']
BLOCKS_PER_DAY = 86400 / BLOCK_TIME
ALGORITHM_PERCENTAGE = {'cuckoo': 0.4, 'progpow': 0.48, 'randomx': 0.48}


class Rig(BaseModel):
    name: str = 'Default Rig'
    hashrate: int | None = Field(..., title='Rig Hashrate in H/s')
    algorithm: str | None = Field(..., title='PoW Algorithm (randomx, progpow, cuckoo)')
    power_consumption: int | None = Field(None, title='Rig power consumption in Watts', gt=0, lt=1_000_0000)

    @validator('algorithm')
    def valid_algo(cls, v):
        if v.lower() not in ALGORITHMS:
            raise ValueError(f'"{v.lower()}" is not a valid PoW algorithm, use one of: {ALGORITHMS}')
        return v

    def formatted_hashrate(self):
        if self.algorithm == "cuckoo":
            data = self.hashrate / 10 ** 9, 'GH/s'
        elif self.algorithm == "progpow":
            data = self.hashrate / 10 ** 6, 'MH/s'
        elif self.algorithm == 'randomx':
            data = self.hashrate / 10 ** 3, 'KH/s'
        else:
            data = self.hashrate, 'H/s'

        return f"{data[0]} {data[1]}"


class Blockchain(BaseModel):
    name: str | None = "Mainnet"
    hash: str | None = Field(None, title='Last Block Hash')
    algo: str | None = Field(..., title='Last Block PoW Algorithm')
    height: int | None = Field(..., title='Last Block Height', gt=0, lt=10_000_0000)
    supply: int | None = Field(None, title='Total Supply Amount in EPIC')
    reward: float | None = Field(..., title='Last Block Reward', gt=0, le=16)
    avg_time: int | None = Field(BLOCK_TIME, title='Average Time for Block in Seconds')
    datetime: dtime | None = Field(None, title='Last Block Time and Date')
    timestamp: int | None = Field(None, title='Last Block Unix Timestamp')
    total_diffs: dict[str, int] | None = Field(None, title='Total Difficulty for Each PoW Algorithm')
    target_diffs: dict[str, int] | None = Field(None, title='Target Difficulty for Each PoW Algorithm')
    network_hashrate: dict[str, int] | None = Field(..., title='Network Hashrate for Each PoW Algorithm')


class Currency(BaseModel):
    symbol: str | None = Field('USD', title='Base currency used fin calculations.')
    btc_price: float | None = Field(..., title='Price in base currency for 1 BTC.')
    epic_price: float | None = Field(..., title='Price in base currency for 1 EPIC.')


class Report(BaseModel):
    rig: Rig | None = Field(...)
    currency: str | None = Field(None, title='Base Currency Used in Calculations')
    epic_per_day: float | None = Field(None, title='Yield in EPIC within 24H')
    blocks_per_day: float | None = Field(None, title='Mined Blocks in 24H')
    hours_for_block: float | None = Field(None, title='Hours Needed to Mine a Block')
    costs: float | None = Field(None, title='Total Costs in EPIC for 24H')
    cost_pool: float | None = Field(None, title='Pool Fee in EPIC for 24H')
    cost_energy: float | None = Field(None, title='Energy Cost in Currency for 24H')
    yield_value: float | None = Field(None, title='Value of Yield in Currency for 24H')
    profit: float | None = Field(None, title='Profit in Currency for 24H')

    def formatted(self):
        return \
            f"""
            REPORT FOR '{self.rig.name}' | PoW: '{self.rig.algorithm.upper()}'  
            HASHRATE: {self.rig.formatted_hashrate()}
            24H YIELD: {self.epic_per_day} EPIC | {round(self.yield_value, 3)} {self.currency}
            24H COSTS: {round(self.costs, 3)} {self.currency}
            24H PROFIT: {round(self.profit, 3)} {self.currency}
            """


class Calculator(BaseModel):
    """
    Store necessary data and provide functions to calculate mining profitability
    """
    rig: Rig | None = Field(..., title='Rig Instance')
    currency: Currency | None = Field(..., title='Base Currency, i.e. USD')
    pool_fee: float | None = Field(None, title='Pool Fee as Percentage')
    blockchain: Blockchain
    electricity_cost: float | None = Field(None, title='Electricity Cost for 1 kW/h')

    def network_hashrate(self) -> int:
        temp_hashrate = self.blockchain.network_hashrate[self.rig.algorithm]

        if self.rig.algorithm == 'cuckoo':
            temp_hashrate *= 10 ** 9

        return temp_hashrate

    def get_exact_reward(self):
        if 698401 < self.blockchain.height <= 1157760:
            return [8.0, 0.5328, 7.4672, 1157760]
        elif 1157761 < self.blockchain.height <= 1224000:
            return [4.0, 0.2664, 3.7336, 2275200]
        elif 1224001 < self.blockchain.height <= 1749600:
            return [4.0, 0.2220, 3.7780, 2275200]
        elif 1749601 < self.blockchain.height <= 2023200:
            return [4.0, 0.1776, 3.8224, 2275200]
        elif 2023201 < self.blockchain.height <= 2275200:
            return [2.0, 0.0888, 1.9112]

    def raw_yield(self) -> dict:
        miners_reward = self.get_exact_reward()[2]

        if self.rig.hashrate and self.rig.algorithm:
            rig_vs_net = self.rig.hashrate / self.network_hashrate()
            algo_blocks_per_day = BLOCKS_PER_DAY * ALGORITHM_PERCENTAGE[self.rig.algorithm]
            rig_blocks_per_day = rig_vs_net * algo_blocks_per_day
            hours_for_block = 24 / rig_blocks_per_day
            epic_amount = rig_blocks_per_day * miners_reward

            response = {
                '24h': round(epic_amount, 8),
                'block_reward': miners_reward,
                'blocks_per_day': round(rig_blocks_per_day, 3),
                'hours_for_block': round(hours_for_block, 1),
                'days_for_block': round(hours_for_block / 24, 1)
                }

            return response

    def pool_cost(self) -> dict:
        """return pool_cost for 24h in EPIC"""
        if self.pool_fee:
            fee = self.raw_yield()['24h'] * (self.pool_fee / 100)
        else:
            fee = 0

        return {'symbol': 'EPIC', 'value': fee}

    def energy_cost(self) -> dict:
        """return energy_cost for 24h in given currency (default USD)"""
        if self.electricity_cost and self.rig.power_consumption is not None:
            mining_time = 24 * ALGORITHM_PERCENTAGE[self.rig.algorithm]
            mining_cost = (self.rig.power_consumption / 1000) * self.electricity_cost
            cost = mining_time * mining_cost
        else:
            cost = 0

        return {'symbol': self.currency.symbol, 'value': cost}

    def income(self, time_in_days: int = 1):
        return {'symbol': self.currency.symbol, 'value': self.currency.epic_price * self.raw_yield()['24h'] * time_in_days}

    def profit(self):
        currency_yield_value = (self.raw_yield()['24h'] - self.pool_cost()['value']) * self.currency.epic_price
        currency_rig_profit = currency_yield_value - self.energy_cost()['value']
        return {'symbol': self.currency.symbol, 'value': currency_rig_profit}

    def get_report(self, as_dict: bool = True):
        raw_yield = self.raw_yield()
        data = {
            'rig': self.rig,
            'currency': self.currency.symbol,

            'epic_per_day': raw_yield['24h'],
            'blocks_per_day': raw_yield['blocks_per_day'],
            'hours_for_block': raw_yield['hours_for_block'],

            'costs': self.pool_cost()['value'] * self.currency.epic_price + self.energy_cost()['value'],
            'cost_pool': self.pool_cost()['value'],
            'cost_energy': self.energy_cost()['value'],

            'profit': self.profit()['value'],
            'yield_value': self.income()['value'],
            }

        if as_dict:
            return Report(**data).dict(exclude={'blockchain'})
        else:
            return Report(**data)


class Parser(BaseModel):
    """Help to parse string queries"""
    query: str | None = Field(None, title="Query message to parse hashrate from.")
    unit: str | None = Field(None, title="Parsed Hashrate Unit")
    pool_fee: int | None = Field(0, title="Mining Pool fee in %")
    hashrate: int | None = Field(None, title="Parsed Hashrate in H/s")
    currency: str | None = Field(None, title="Parsed Currency")
    algorithm: str | None = Field(None, title="Parsed PoW Algorithm")
    consumption: float | int = Field(None, title="Parsed Energy Consumption in Watts")
    energy: float | int = Field(None, title="Parsed Energy Unit Price in Currency")

    _PATTERNS = {
        'mining_algorithms': {
            'progpow': ('Pp', 'pp', 'progpow', 'ProgPow', 'PROGPOW', 'Progpow'),
            'randomx': ('Rx', 'rx', 'randomx', 'RANDOMX', 'RandomX', 'Randomx', 'randomX'),
            'cuckoo': ('cu', 'ck', 'co', 'cuckoo', 'Cuckoo', 'CUCKOO')
            },
        'units': {
            'hash': ('h', 'H'),
            'kilohash': ('kh', 'Kh', 'KH'),
            'megahash': ('mh', 'Mh', 'MH'),
            'gigahash': ('gh', 'Gh', 'GH')
            }}

    @validator('query')
    def split_query(cls, query):
        if isinstance(query, (int, float)):
            query = str(query)
        return query.split(' ')

    def get_algo(self):
        """Find what kind of algorithm is provided and save"""
        algo = None
        if any(x in self.query for x in self._PATTERNS['mining_algorithms']['progpow']):
            algo = 'progpow'
        if any(x in self.query for x in self._PATTERNS['mining_algorithms']['randomx']):
            algo = 'randomx'
        if any(x in self.query for x in self._PATTERNS['mining_algorithms']['cuckoo']):
            algo = 'cuckoo'

        self.algo = algo

    def _units(self, source=None):
        """Find what kind of unit is provided and save"""
        if not source:
            source = self.query

        for unit in self._PATTERNS['units']:
            for key in self._PATTERNS['units'][unit]:
                for match in source:
                    if key in match:
                        self.unit = unit

    def get_units(self) -> tuple[str, int]:
        if self.unit == "kilohash":
            return 'KH/s', 10 ** 3
        elif self.unit == "megahash":
            return 'MH/s', 10 ** 6
        elif self.unit == "gigahash":
            return 'GH/s', 10 ** 9
        else:
            return 'H/s', 1

    def get_hashrate(self):
        """Find rig hashrate given by user and return it"""
        if isinstance(self.hashrate, int) and self.hashrate > 1:
            self.unit = 'hash'
            print(f'{self.hashrate} provided in H/s')
            print(self)
            return

        pat = re.compile(r"\d*\.?\d+|[-+]?\d+")
        temp_hashrate = list(filter(pat.match, self.query))

        if temp_hashrate:
            value = float(re.search(r"\d*\.?\d+|[-+]?\d+", temp_hashrate[0]).group())

            self._units()
            if not self.unit:
                temp_unit = [temp_hashrate[0].split('value')]
                self._units(temp_unit)

                if self.unit:
                    # print(f'Unit found without space, {self.unit}')
                    pass
                else:
                    self.unit = 'hash'
                    # print('No unit found in message, using H/s')

            hashrate = value * self.get_units()[1]
            print(f"PARSED HASHRATE: {value} UNIT: {self.unit} ({hashrate} H/s)")
            self.hashrate = hashrate
        else:
            print(f'No hashrate found in {self.query}')

    def result(self) -> dict:
        """Update parsed data and return as dict"""
        self.get_algo()
        self.get_hashrate()
        return self.dict()