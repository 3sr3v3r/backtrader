from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from datetime import datetime, timedelta

from backtrader.feed import DataBase
from backtrader import TimeFrame, date2num, num2date
from backtrader.utils.py3 import (integer_types, queue, string_types,
                                  with_metaclass)
from backtrader.metabase import MetaParams

import backtrader as bt
from btplotting import BacktraderPlottingLive
from btplotting.schemes import Tradimo
from OandaStrategy import OandaTest
import btoandav20
import json

if __name__ == '__main__':
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    # Add a strategy
    cerebro.addstrategy(OandaTest)

    with open("config.json", "r") as file:
        config = json.load(file)

    storekwargs = dict(
        token=config["oanda"]["token"],
        account=config["oanda"]["account"],
        practice=config["oanda"]["practice"],
        notif_transactions=True,
        stream_timeout=10,
    )

    oandastore = btoandav20.stores.OandaV20Store(**storekwargs)
    broker = oandastore.getbroker()

    datakwargs = dict(
        timeframe=(bt.TimeFrame.Minutes),
        compression=1,
        tz='Europe/Berlin',
        backfill=False,
        backfill_start=True,
    )

    data = oandastore.getdata(dataname="EUR_USD", **datakwargs)
    data.resample(
      timeframe=bt.TimeFrame.Minutes,
      compression=1)



    cerebro.adddata(data)
    cerebro.setbroker(broker)
    cerebro.addanalyzer(BacktraderPlottingLive, scheme=Tradimo(), lookback=120)



    cerebro.run()

    # Plot the result
    cerebro.plot()


