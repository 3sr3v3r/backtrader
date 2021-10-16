from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import backtrader as bt
import backtrader.feeds as btfeeds
from ma_strategy import MaStrategy



if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(MaStrategy)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, '.\\data\\oanda_XAU_USD_M1.csv')

    # Create a Data Feed
    data = btfeeds.GenericCSVData(
        dataname=datapath,
        # Do not pass values before this date
        fromdate=datetime.datetime(2021, 4, 1),
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
    cerebro.adddata(data)
    cerebro.resampledata(data,timeframe=bt.TimeFrame.Minutes, compression=60)
    #cerebro.resampledata(data,timeframe=bt.TimeFrame.Minutes, compression=240)
    #erebro.resampledata(data, timeframe=bt.TimeFrame.Days, compression=1)

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
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    portvalue = cerebro.broker.getvalue()
    pnl = portvalue - startcash

    print('Final Portfolio Value: ${}'.format(portvalue))
    print('P/L: ${}'.format(pnl))


    # Plot the result
    cerebro.plot(style='candle')