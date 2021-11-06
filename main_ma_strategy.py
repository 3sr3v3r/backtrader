from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

# Import the backtrader platform
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.analyzers as btanalyzers
from ma_strategy import MaStrategy


if __name__ == '__main__':

    def printTradeAnalysis(analyzer):
        '''
        Function to print the Technical Analysis results in a nice format.
        '''
        # Get the results we are interested in
        total_open = analyzer.total.open
        total_closed = analyzer.total.closed
        total_won = analyzer.won.total
        total_lost = analyzer.lost.total
        win_streak = analyzer.streak.won.longest
        lose_streak = analyzer.streak.lost.longest
        pnl_net = round(analyzer.pnl.net.total, 2)
        strike_rate = round((total_won / total_closed) * 100, 2)
        # Designate the rows
        h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
        h2 = ['Strike Rate', 'Win Streak', 'Losing Streak', 'PnL Net']
        r1 = [total_open, total_closed, total_won, total_lost]
        r2 = [strike_rate, win_streak, lose_streak, pnl_net]
        # Check which set of headers is the longest.
        if len(h1) > len(h2):
            header_length = len(h1)
        else:
            header_length = len(h2)
        # Print the rows
        print_list = [h1, r1, h2, r2]
        row_format = "{:<15}" * (header_length + 1)
        print("Trade Analysis Results:")
        for row in print_list:
            print(row_format.format('', *row))

    optimizations = 0
    dataframe_collection = {}

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    # cerebro.addstrategy(MaStrategy)
    strats = cerebro.optstrategy(
        MaStrategy,
        ma_mid=range(22, 23),
        ma_short=range(5, 6)
        )

    # Analyzer
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='mytrade')

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '.\\data\\oanda_EUR_USD_M1.csv')

    # Create a Data Feed
    data = btfeeds.GenericCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2019, 1, 1),
        # Do not pass values before this date
        todate=datetime.datetime(2021, 10, 7),
        # Do not pass values after this date
        reverse=False,
        timeframe=bt.TimeFrame.Minutes,
        compresion=1,
        nullvalue=0.0,

        dtformat='%Y-%m-%dT%H:%M:%S.%f000Z',

        datetime=0,
        time=-1,
        open=1,
        high=2,
        low=3,
        close=4,
        volume=5,
        openinterest=-1
    )

    # Add the Data Feed to Cerebro
    #cerebro.adddata(data)
    #cerebro.resampledata(data,timeframe=bt.TimeFrame.Minutes, compression=60)
    #cerebro.resampledata(data,timeframe=bt.TimeFrame.Minutes, compression=240)
    #erebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=1)


    cerebro.replaydata(data,timeframe=bt.TimeFrame.Minutes, compression=60)

    # Variable for our starting cash
    startcash = 10000
    # Set our desired cash start

    cerebro.broker.setcash(startcash)

    # Set commission
    cerebro.broker.setcommission(leverage=50)

    # Add a FixedSize sizer according to the stake
    #cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())


    # Run over everything
    stratruns = cerebro.run(preload=True, maxcpus=4, optreturn=False)

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - startcash

    print('Final Portfolio Value: ${}'.format(portvalue))
    print('P/L: ${}'.format(pnl))

    print('==================================================')
    for stratrun in stratruns:
        print('**************************************************')
        for strat in stratrun:
            print('--------------------------------------------------')
            print(strat.p._getkwargs())
            analysis = strat.analyzers.mytrade.get_analysis()
            printTradeAnalysis(analysis)
            dataframe_collection[optimizations] = strat.trade_overview
            #for key, value in analysis.items():
            #    print("Key: {}, Value: {}".format(key, value))
            optimizations += 1

    print('==================================================')

    for optimization_run in dataframe_collection:
        trade_overview = dataframe_collection[optimization_run]
        print(trade_overview.dtypes)
        trade_overview["datetime"] = pd.to_datetime(trade_overview["datetime"], infer_datetime_format=True).dt.hour
        trade_overview = trade_overview.groupby(trade_overview["datetime"]).sum().reset_index()
        print(trade_overview)
        trade_overview.plot(kind='bar', x='datetime', y='profit')
        plt.show()

        # plot it



    # Plot the result
    #cerebro.plot(style='candle')

