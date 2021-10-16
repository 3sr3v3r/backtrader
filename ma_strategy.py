import backtrader as bt
from datetime import datetime


class MaStrategy(bt.Strategy):
    '''
    This strategy contains some additional methods that can be used to calcuate
    whether a position should be subject to a margin close out from Oanda.
    '''
    params = (('size', 5000), ('ma_long', 150), ('ma_mid', 25), ('ma_short', 6))

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or datetime.combine(self.data.datetime.date(),self.data.datetime.time())
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.order = None
        self.log_line = False
        self.dataclose = self.datas[0].close
        self.count = 0
        self.execution_price = 0
        self.execution_size = 0
        self.execution_direction = 0
        self.signal = None

        self.rsi = bt.indicators.RSI_Safe(self.dataclose)
        self.ma_long = bt.indicators.MovingAverageSimple(self.data1.close, period=self.p.ma_long)
        self.ma_mid = bt.indicators.MovingAverageSimple(self.data1.close, period=self.p.ma_mid)
        self.ma_short = bt.indicators.MovingAverageSimple(self.data1.close, period=self.p.ma_short)

        # Indicators for the plotting show
        bt.indicators.ATR(self.datas[0], plot=True)
        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF:', msg)

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF:', data._getstatusname(status), *args)
        if status == data.LIVE:
            pass

    def start(self):
        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']
        print(', '.join(header))



    def next(self):
        bar = len(self.data)
        self.dt = datetime.combine(self.data.datetime.date(),self.data.datetime.time())
        if self.log_line:
            txt = list()
            txt.append('Data0')
            txt.append('%04d' % len(self.data))
            dtfmt = '%Y-%m-%dT%H:%M:%S'
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            txt.append('{:f}'.format(self.data0.open[0]))
            txt.append('{:f}'.format(self.data0.high[0]))
            txt.append('{:f}'.format(self.data0.low[0]))
            txt.append('{:f}'.format(self.data0.close[0]))
            txt.append('{:6d}'.format(int(self.data0.volume[0])))
            print(', '.join(txt))

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        if not self.position:
            # Determine the direction of the trade
            if len(self.data0) > self.p.ma_long:
                if self.ma_mid[0] > self.ma_long[0] and self.ma_short[0] > self.ma_long[0]:
                    self.direction = 'long'
                elif self.ma_mid[0] < self.ma_long[0] and self.ma_short[0] < self.ma_long[0]:
                    self.direction = 'short'
                else:
                    self.direction = None

                if self.direction == 'long':
                    if self.ma_short[-1] < self.ma_mid[-1] and self.ma_short[0] > self.ma_mid[0]:
                        self.log("LONG!! ma_short: " + str(self.ma_short[-1]) + "ma_mid: " + str(self.ma_mid[-1]))
                        self.signal = 'long'
                if self.direction == 'short':
                    if self.ma_short[-1] > self.ma_mid[-1] and self.ma_short[0] < self.ma_mid[0]:
                        self.log("SHORT!! ma_short: " + str(self.ma_short[-1]) + "ma_mid: " + str(self.ma_mid[-1]))
                        self.signal = 'short'

            if self.signal == 'long':
                # self.log('BUY TIME!!!')
                self.cash_before = self.broker.getcash()
                #self.log('Position open: %s.' % self.position)
                size = self.p.size / self.dataclose[0]
                self.order = self.buy(size=size)
                self.execution_direction = "long"
                self.log('Size =  %.2f' % size)
                self.order.addinfo(name='Entry')
                self.signal = None
            elif self.signal == 'short':
                #self.log('SELL TIME!!!')
                #self.log('Position open: %s.' % self.position)
                self.cash_before = self.broker.getcash()
                size = self.p.size / self.dataclose[0]
                self.order = self.sell(size=size)
                self.execution_direction = "short"
                self.log('Size =  %.2f' % size)
                self.order.addinfo(name='Entry')
                self.signal = None
        else:
            '''
            First check if margin close out conditions are met. If not, check
            to see if we should close the position through the strategy rules.

            If a close out occurs, we need to addinfo to the order so that we
            can log it properly later
            '''
            mco_result = self.check_mco(
                value=self.broker.get_value(),
                margin_used=self.margin
            )

            if mco_result == True:
                close = self.close()
                close.addinfo(name='MCO')

            elif self.execution_direction == 'long':
                if (self.dataclose[0] / self.execution_price) >= 1.03:
                    self.log('Take profit LONG')
                    self.log('Execution price: {}'.format(self.execution_price))
                    self.log('Closing price: {}'.format(self.dataclose[0]))
                    self.log('Profit / Loss: {}'.format(self.dataclose[0] / self.execution_price))
                    self.order = self.close()
                    self.order.addinfo(name='Close')
                elif (self.dataclose[0] / self.execution_price) <= 0.97:
                    self.log('Stop loss LONG')
                    self.log('Execution price: {}'.format(self.execution_price))
                    self.log('Closing price: {}'.format(self.dataclose[0]))
                    self.log('Profit / Loss: {}'.format(self.dataclose[0] / self.execution_price))
                    self.order = self.close()
                    self.order.addinfo(name='Close')

            elif self.execution_direction == 'short':
                if (self.execution_price / self.dataclose[0]) >= 1.03:
                    self.log('Take profit SHORT')
                    self.log('Execution price: {}'.format(self.execution_price))
                    self.log('Closing price: {}'.format(self.dataclose[0]))
                    self.log('Profit / Loss: {}'.format(self.execution_price / self.dataclose[0]))
                    self.order = self.close()
                    self.order.addinfo(name='Close')
                elif (self.execution_price / self.dataclose[0])  <= 0.97 :
                    self.log('Stop loss SHORT')
                    self.log('Execution price: {}'.format(self.execution_price))
                    self.log('Closing price: {}'.format(self.dataclose[0]))
                    self.log('Profit / Loss: {}'.format(self.execution_price / self.dataclose[0]))
                    self.order = self.close()
                    self.order.addinfo(name='Close')

        self.count += 1

    def notify_trade(self, trade):
        if trade.isclosed:
            print('{}: Trade closed '.format(self.dt))
            print('{}: PnL Gross {}, Net {}\n\n'.format(self.dt,
                                                round(trade.pnl,2),
                                                round(trade.pnlcomm,2)))

    def notify_order(self,order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        if order.status in [order.Completed, order.Partial]:
            self.execution_price = order.executed.price
            self.execution_size = order.executed.size
            self.total_value = self.execution_price * self.execution_size
            leverage = self.broker.getcommissioninfo(self.data).get_leverage()
            self.margin = abs((self.execution_price * self.execution_size) / leverage)

            if 'name' in order.info:
                if order.info['name'] == 'Entry':
                    print('{}: Entry Order Completed '.format(self.dt))
                    print('{}: Order Executed Price: {}, Executed Size {}'.format(self.dt,self.execution_price,self.execution_size))
                    print('{}: Position Value: {} Margin Used: {}'.format(self.dt,self.total_value,self.margin))
                elif order.info['name'] == 'MCO':
                    print('{}: WARNING: Margin Close Out'.format(self.dt))
                else:
                    print('{}: Close Order Completed'.format(self.dt))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def check_mco(self, value, margin_used):
        '''
        Make a check to see if the margin close out value has fallen below half
        of the margin used, close the position.

        value: value of the portfolio for a given data. This is essentially the
        same as the margin close out value which is balance + pnl
        margin_used: Initial margin
        '''

        if value < (margin_used /2):
            return True
        else:
            return False