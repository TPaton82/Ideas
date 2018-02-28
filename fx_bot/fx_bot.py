
from api_calls import get, stream, post
import json
import pandas as pd
import numpy as np
import seaborn as sns
import strategies
import matplotlib.pyplot as plt


class FXBot(object):
    def __init__(self):
        self.position = 0
        self.df = pd.DataFrame()
        self.connected = True
        self.balance = self.get_account_balance()
        self.units = self.balance / 100.0

    @staticmethod
    def get_account_balance(**params):
        # Get account balance
        summary = get("summary", params)
        balance = pd.to_numeric(summary['account']['balance'])
        return balance

    def update_account_balance(self):
        # Update account balance
        self.balance = self.get_account_balance()

    def update_units(self):
        # Update units
        self.units = self.balance / 100.0

    def update_account_data(self):
        # Update account data
        self.update_account_balance()
        self.update_units()

    @staticmethod
    def get_position(**params):
        # Get positions from api
        positions = get("openPositions", params)
        return positions

    @staticmethod
    def get_instrument(**params):
        # Get instrument from api
        instrument = get("instruments", params)
        return instrument

    @staticmethod
    def get_price(**params):
        # Get price stream for given instrument
        price = get("pricing", params)
        return price

    @staticmethod
    def create_order(side, instrument, units, type='MARKET'):
        if side == 'buy':
            units = abs(int(units))
        elif side == 'sell':
            units = int(units) * -1
        else:
            raise Exception('order type not recognised, use buy or sell!')

        params = {
            'instrument': instrument,
            'units': units,
            'type': type
        }

        # Create an order
        order = post("orders", params)

        print('\n', order)

    def on_success(self, data, instrument, strat, strat_params):
        # appends the new tick data to the DataFrame object
        self.df = self.df.append(data)
        # transforms the time information to a DatetimeIndex object
        self.df.index = pd.DatetimeIndex(self.df['time'])
        # resamples the data set to a new, homogeneous interval
        dfr = self.df.resample('1T').last().dropna()

        # run the given strategy
        strategy_to_run = getattr(strategies, strat)
        output = strategy_to_run(dfr, strat_params)

        if output == 'buy':
            # go long
            if self.position == 0:
                self.create_order('buy', instrument, self.units)
            elif self.position == -1:
                self.create_order('buy', instrument, self.units * 2)
            self.position = 1
        elif output == 'sell':
            # go short
            if self.position == 0:
                self.create_order('sell', instrument, self.units)
            elif self.position == 1:
                self.create_order('sell', instrument, self.units * 2)
            self.position = -1

    def get_history(self, **params):
        # Get price history for given instrument
        history = get("candles", params)['candles']

        # Insert data in DataFrame
        df = pd.DataFrame(history)

        # pull out the close ask prices
        df['closeAsk'] = df['ask'].apply(self.get_close)
        df['closeBid'] = df['bid'].apply(self.get_close)
        df['closeMid'] = df['mid'].apply(self.get_close)

        # convert columns to required formats
        df['time'] = pd.to_datetime(df['time'])
        df['closeAsk'] = pd.to_numeric(df['closeAsk'])
        df['closeBid'] = pd.to_numeric(df['closeBid'])
        df['closeMid'] = pd.to_numeric(df['closeMid'])

        return df[['closeAsk', 'closeMid', 'closeBid', 'time']]

    def seed_history(self, data):
        if not self.df.empty:
            raise Exception('DataFrame not empty, clear first!')

        data.rename(columns={'closeAsk': 'ask', 'closeBid': 'bid'}, inplace=True)

        self.df = data

    @staticmethod
    def test_strategy(input_df, momentum_list):
        sns.set()
        input_df['returns'] = np.log(input_df['closeAsk'] / input_df['closeAsk'].shift(1))

        cols = []
        for m in momentum_list:
            col = 'position_%s' % m
            input_df[col] = np.sign(input_df['returns'].rolling(m).mean())
            cols.append(col)

        strats = ['returns']

        for col in cols:
            strat = 'strategy_%s' % col.split('_')[1]
            input_df[strat] = input_df[col].shift(1) * input_df['returns']
            strats.append(strat)

        input_df[strats].dropna().cumsum().apply(np.exp).plot()
        plt.show()

    @staticmethod
    def get_close(dic):
        return dic.get('c', None)

    def get_price_stream(self, **params):
        # Get price stream for given instrument
        price_stream = stream("pricing/stream", params)

        instrument = params.get('instruments')

        strategy = params.get('strategy')

        strat_params = params.get('strat_params')

        for line in price_stream.iter_lines():
            if not self.connected:
                break
            if line:
                resp = json.loads(line.decode("utf-8"))
                if resp['type'] == 'HEARTBEAT':
                    pass
                elif resp['type'] == 'PRICE':
                    ask = float(resp['asks'][0]['price'])
                    bid = float(resp['bids'][0]['price'])
                    time = pd.to_datetime(resp['time'])
                    df = pd.DataFrame([{'bid': bid, 'ask': ask, 'time': time}])
                    self.on_success(df, instrument, strategy, strat_params)

    def disconnect(self):
        self.connected = False
