from decimal import Decimal
from typing import Union


class MiningYield:
    def __init__(self, rig):
        self.rig = rig

    def _height(self) -> int:
        return int(self.rig.updated_block['height'])

    def _rig_vs_net(self):
        return self.rig.hashrate / self._network_hashrate()

    def _target_diff(self) -> Decimal:
        return Decimal(self.rig.updated_block['target_diffs'][self.rig.algorithm])

    def _block_reward(self) -> list:
        return self.rig.blockchain_.get_exact_reward(self._height())

    def _algo_percentage(self) -> Decimal:
        return Decimal(self.rig.blockchain_.ALGORITHM_PERCENTAGE[self.rig.algorithm])

    def _network_hashrate(self) -> Decimal:
        temp_hashrate = self.rig.updated_block['network_hashrate'][self.rig.algorithm]

        if self.rig.algorithm == 'cuckoo':
            temp_hashrate *= 10 ** 9

        return Decimal(temp_hashrate)

    def _algo_blocks_per_day(self) -> Decimal:
        return Decimal(self.rig.blockchain_.BLOCKS_PER_DAY * self._algo_percentage())

    def reward(self) -> dict:
        miners_reward = Decimal(self._block_reward()[2])

        if self.rig.hashrate and self.rig.algorithm:
            rig_blocks_per_day = self._rig_vs_net() * self._algo_blocks_per_day()
            hours_for_block = 24 / rig_blocks_per_day
            epic_amount = rig_blocks_per_day * miners_reward

            response = {
                '24h': epic_amount,
                'block_reward': miners_reward,
                'blocks_per_day': rig_blocks_per_day,
                'hours_for_block': hours_for_block,
                }

            return response


class MiningCost:
    def __init__(self, rig):
        self.rig = rig

    def _pool(self) -> Decimal:
        if self.rig.pool_fee:
            fee = self.rig.reported_yield['24h'] * (self.rig.pool_fee / 100)
        else:
            fee = 0

        return Decimal(fee)

    def _energy(self) -> Decimal:
        if self.rig.electricity_cost and self.rig.power_consumption is not None:
            mining_time = Decimal(24 * self.rig.blockchain_.ALGORITHM_PERCENTAGE[self.rig.algorithm])
            mining_cost = (self.rig.power_consumption / 1000) * self.rig.electricity_cost
            cost = mining_time * mining_cost
        else:
            cost = 0

        return Decimal(cost)

    def total(self):
        return {'energy': self._energy(), 'pool': self._pool()}


class MiningProfit:
    def __init__(self, rig):
        self.rig = rig
        self.epic_price = self.rig.market_().price_epic_vs(self.rig.currency)

    def income(self):
        epic_amount = self.rig.reported_yield['24h']
        income_24h = self.epic_price * epic_amount
        btc_value = self.rig.market_.currency_to_btc(income_24h, self.rig.currency)

        response = {'currency_value': Decimal(income_24h),
                    'btc_value': Decimal(btc_value)}

        return response

    def profit(self):
        epic_pool_cost = self.rig.reported_costs['pool']
        currency_pool_cost = epic_pool_cost * self.epic_price

        currency_yield_value = (self.rig.reported_yield['24h'] - epic_pool_cost) * self.epic_price
        currency_energy_cost = self.rig.reported_costs['energy']

        currency_total_cost = currency_energy_cost + currency_pool_cost
        currency_rig_profit = currency_yield_value - currency_total_cost

        btc_rig_profit = self.rig.market_().currency_to_btc(currency_rig_profit, self.rig.currency)

        response = {
            'currency_rig_profit': currency_rig_profit,
            'btc_rig_profit': btc_rig_profit,
            'currency_yield_value': currency_yield_value,
            'currency_pool_cost': currency_pool_cost,
            'currency_energy_cost': currency_energy_cost,
            }

        return response


class Rig:
    """Rig instance"""
    def __init__(self,
                 hashrate: Union[Decimal, int, float, str],
                 algorithm: str,
                 hardware: str = None,
                 pool_fee: Union[Decimal, int, float, str] = 0,
                 electricity_cost: Union[Decimal, int, float, str] = 0,
                 power_consumption: Union[Decimal, int, float, str] = 0,
                 currency: str = None,
                 ):

        self.hashrate = Decimal(hashrate)
        self.currency = currency if currency else 'USD'
        self.pool_fee = Decimal(pool_fee)
        self.hardware = hardware
        self.algorithm = algorithm.lower()
        self.electricity_cost = Decimal(electricity_cost)
        self.power_consumption = Decimal(power_consumption)
        #
        # self.market_ = MarketData
        # self.blockchain_ = Blockchain

        self.updated_block: dict = {}
        self.reported_yield: dict = {}
        self.reported_costs: dict = {}
        self.reported_profit: dict = {}

    def _report(self):
        self.updated_block = Database().get_last_block_data()
        self.reported_yield = MiningYield(rig=self).reward()
        self.reported_costs = MiningCost(rig=self).total()
        self.reported_profit = MiningProfit(rig=self).profit()
        # print(f"Rig instance updated")

    def get_report(self):
        self._report()

        response = {
            'currency': self.currency,
            '24h yield': self.reported_yield['24h'],
            'blocks_per_day': self.reported_yield['blocks_per_day'],
            'hours_for_block': self.reported_yield['hours_for_block'],
            'cost_pool': self.reported_costs['pool'],
            'cost_energy': self.reported_costs['energy'],
            'currency_rig_profit': self.reported_profit['currency_rig_profit'],
            'btc_rig_profit': self.reported_profit['btc_rig_profit'],
            'currency_yield_value': self.reported_profit['currency_yield_value'],
            'currency_pool_cost': self.reported_profit['currency_pool_cost'],
            'currency_energy_cost': self.reported_profit['currency_energy_cost'],
            }

        return response