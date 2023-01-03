"""
Models to store and process data using 'pydantic' library.
"""

from datetime import datetime as dtime
from typing import Union
import re

from pydantic import BaseModel, Field, validator

from . import (
    ALGORITHMS,
    BLOCK_TIME,
    BLOCKS_PER_DAY,
    ALGORITHM_PERCENTAGE
    )


class Rig(BaseModel):
    name: str = 'Default Rig'
    hashrate: Union[int, None] = Field(..., title='Rig Hashrate in H/s')
    algorithm: Union[str, None] = Field(..., title='PoW Algorithm (randomx, progpow, cuckoo)')
    power_consumption: Union[int, None] = Field(None, title='Rig power consumption in Watts', lt=1_000_0000)

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
    name: Union[str, None] = "Mainnet"
    hash: Union[str, None] = Field(None, title='Last Block Hash')
    algo: Union[str, None] = Field(..., title='Last Block PoW Algorithm')
    height: Union[int, None] = Field(..., title='Last Block Height', gt=0, lt=10_000_0000)
    supply: Union[int, None] = Field(None, title='Total Supply Amount in EPIC')
    reward: Union[float, None] = Field(..., title='Last Block Reward', gt=0, le=16)
    avg_time: Union[int, None] = Field(BLOCK_TIME, title='Average Time for Block in Seconds')
    datetime: Union[dtime, None] = Field(None, title='Last Block Time and Date')
    timestamp: Union[int, None] = Field(None, title='Last Block Unix Timestamp')
    total_diffs: Union[dict[str, int], None] = Field(None, title='Total Difficulty for Each PoW Algorithm')
    target_diffs: Union[dict[str, int], None] = Field(None, title='Target Difficulty for Each PoW Algorithm')
    network_hashrate: Union[dict[str, int], None] = Field(..., title='Network Hashrate for Each PoW Algorithm')


class Currency(BaseModel):
    symbol: Union[str, None] = Field('USD', title='Base currency used fin calculations.')
    btc_price: Union[float, None] = Field(..., title='Price in base currency for 1 BTC.')
    epic_price: Union[float, None] = Field(..., title='Price in base currency for 1 EPIC.')


class Report(BaseModel):
    rig: Union[Rig, None] = Field(...)
    currency: Union[str, None] = Field(..., title='Currency Used in Calculations')
    epic_price: Union[float, int, None] = Field(..., title='EPIC Price in Given Currency')
    coins_per_day: Union[list[str, float], None] = Field([None, 0], title='Yield in EPIC within 24H')
    blocks_per_day: Union[list[str, float], None] = Field([None, 0], title='Mined Blocks in 24H')
    hours_for_one_block: Union[list[str, float], None] = Field([None, 0], title='Hours Needed to Mine One Block')
    cost_energy: Union[list[str, float], None] = Field([None, 0], title='Energy Cost in Currency for 24H')
    cost_pool: Union[list[str, float], None] = Field([None, 0], title='Pool Fee in EPIC for 24H')
    cost_total: Union[list[str, float], None] = Field([None, 0], title='Total Costs in EPIC for 24H')
    value_per_day: Union[list[str, float], None] = Field([None, 0], title='Value of Yield in Currency for 24H')
    profit_per_day: Union[list[str, float], None] = Field([None, 0], title='Profit in Currency for 24H')

    def formatted(self):
        return \
            f"""
            REPORT FOR '{self.rig.name}' | PoW: '{self.rig.algorithm.upper()}'  
            HASHRATE: {self.rig.formatted_hashrate()}
            24H YIELD: {self.coins_per_day[1]} EPIC | {round(float(self.value_per_day[1]), 3)} {self.currency}
            24H COSTS: {round(float(self.cost_total[1]), 3)} {self.currency}
            24H PROFIT: {round(float(self.profit_per_day[1]), 3)} {self.currency}
            """


class Calculator(BaseModel):
    """
    Store necessary data and provide functions to calculate mining profitability
    """
    rig: Union[Rig, None] = Field(..., title='Rig Instance')
    currency: Union[Currency, None] = Field(..., title='Base Currency, i.e. USD')
    pool_fee: Union[float, None] = Field(0, title='Pool Fee as Percentage')
    blockchain: Blockchain
    energy_price: Union[float, None] = Field(0, title='Electricity Cost for 1 kW/h')

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
                'per_day': round(epic_amount, 8),
                'block_reward': miners_reward,
                'blocks_per_day': round(rig_blocks_per_day, 3),
                'hours_for_block': round(hours_for_block, 1),
                'days_for_block': round(hours_for_block / 24, 1)
                }

            return response

    def pool_cost(self) -> list:
        """return pool_cost for 24h in EPIC"""
        if self.pool_fee:
            fee = self.raw_yield()['per_day'] * (self.pool_fee / 100)
        else:
            fee = 0

        return ['EPIC',  fee]

    def energy_cost(self) -> list:
        """return energy_cost for 24h in given currency (default USD)"""
        if self.energy_price and self.rig.power_consumption is not None:
            mining_time = 24 * ALGORITHM_PERCENTAGE[self.rig.algorithm]
            mining_cost = (self.rig.power_consumption / 1000) * self.energy_price
            cost = mining_time * mining_cost
        else:
            cost = 0
        return [self.currency.symbol, cost]

    def total_cost(self) -> list:
        cost = self.pool_cost()[1] * self.currency.epic_price + self.energy_cost()[1]
        return [self.currency.symbol, cost]

    def income(self, time_in_days: int = 1):
        day_income = (self.raw_yield()['per_day'] - self.pool_cost()[1]) * self.currency.epic_price
        return [self.currency.symbol, day_income * time_in_days]

    def profit(self, time_in_days: int = 1):
        currency_yield_value = (self.raw_yield()['per_day'] - self.pool_cost()[1]) * self.currency.epic_price
        currency_rig_profit = currency_yield_value - self.energy_cost()[1]
        return [self.currency.symbol, currency_rig_profit * time_in_days]

    def get_report(self, as_dict: bool = True):
        raw_yield = self.raw_yield()
        coins_per_day = ['EPIC', raw_yield['per_day']]
        blocks_per_day = ['block', raw_yield['blocks_per_day']]
        hours_for_one_block = ['hour', raw_yield['hours_for_block']]

        data = {
            'rig': self.rig,
            'currency': self.currency.symbol,
            'epic_price': self.currency.epic_price,

            'coins_per_day': coins_per_day,
            'value_per_day': self.income(),
            'blocks_per_day': blocks_per_day,
            'hours_for_one_block': hours_for_one_block,

            'cost_energy': self.energy_cost(),
            'cost_pool': self.pool_cost(),
            'cost_total': self.total_cost(),

            'profit_per_day': self.profit()
            }

        if as_dict:
            print(data)
            return Report(**data).dict()
        else:
            return Report(**data)


class Parser(BaseModel):
    """Help to parse string queries"""
    query: Union[str, None] = Field(None, title="Query message to parse hashrate from.")
    unit: Union[str, None] = Field(None, title="Parsed Hashrate Unit")
    pool_fee: Union[int, None] = Field(0, title="Mining Pool fee in %")
    hashrate: Union[int, float, None] = Field(None, title="Parsed Hashrate in H/s")
    currency: Union[str, None] = Field(None, title="Parsed Currency")
    algorithm: Union[str, None] = Field(None, title="Parsed PoW Algorithm")
    power_consumption: Union[float, int] = Field(None, title="Parsed Energy Consumption in Watts")
    energy_price: Union[float, int] = Field(None, title="Parsed Energy Unit Price in Currency")

    _PATTERNS = {
        'mining_algorithms': {
            'progpow': ('Pp', 'pp', 'progpow', 'ProgPow', 'PROGPOW', 'Progpow'),
            'randomx': ('Rx', 'rx', 'randomx', 'RANDOMX', 'RandomX', 'Randomx', 'randomX'),
            'cuckoo': ('cu', 'ck', 'co', 'cuckoo', 'Cuckoo', 'CUCKOO')
            },
        'units': {
            # 'hash': ('h', 'H'),
            'kilohash': ('kh', 'Kh', 'KH'),
            'megahash': ('mh', 'Mh', 'MH'),
            'gigahash': ('gh', 'Gh', 'GH')
            }}

    @validator('query')
    def split_query(cls, query):
        if isinstance(query, (int, float)):
            query = str(query)
        return query.split(' ')

    def get_algo(self, query=None):
        """Find what kind of algorithm is provided and save"""
        if self.algorithm: return

        algo = None
        if any(x in query for x in self._PATTERNS['mining_algorithms']['progpow']):
            algo = 'progpow'
        if any(x in query for x in self._PATTERNS['mining_algorithms']['randomx']):
            algo = 'randomx'
        if any(x in query for x in self._PATTERNS['mining_algorithms']['cuckoo']):
            algo = 'cuckoo'

        self.algorithm = algo

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
        if isinstance(self.hashrate, (int, float)) and self.hashrate > 0:
            if not self.unit:
                self.unit = 'hash'
                print(f'no units, {self.unit}')
                print(f'{self.hashrate} {self.get_units()[0]} ({self.unit})')

            else:
                print(f'found units: {self.unit}')
                self._units(source=[self.unit])
                print(f'{self.hashrate} {self.get_units()[0]} ({self.unit})')
                self.hashrate = int(self.hashrate * self.get_units()[1])

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

            hashrate = int(value * self.get_units()[1])
            print(f"PARSED HASHRATE: {value} UNIT: {self.unit} ({hashrate} H/s)")
            self.hashrate = hashrate
        else:
            print(f'No hashrate found in {self.query}')

    def parse(self) -> None:
        """Update parsed data"""
        self.get_algo()
        self.get_hashrate()

    def result(self) -> dict:
        return self.dict()