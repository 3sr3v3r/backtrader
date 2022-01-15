from oandapyV20 import API
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
import oandapyV20.endpoints.accounts as accounts
import pandas as pd
import json

#instruments = ['XAU_USD','NL25_EUR']
instruments = ['NAS100_USD']
granularity = "M1"
_from = "2019-01-01T00:00:00Z"
#_from = "2021-05-01T00:00:00Z"
_to= "2021-01-14T00:00:00Z"
price = "A"
# 'A' stands for ask price; if you want to get Bid use 'B' instead or 'AB' for both.

download = True
show_instruments = False

with open("config.json", "r") as file:
    config = json.load(file)

token = config["oanda"]["token"]
accountID = config["oanda"]["account"]
client = API(access_token=token)

if show_instruments:
    r = accounts.AccountInstruments(accountID=accountID)
    rv = client.request(r)
    dataframe = pd.json_normalize(rv, record_path=['instruments'])
    dataframe.to_csv('./data/oanda_instruments.csv', index=False)


if download:
    params = {
       "from": _from,
       "granularity": granularity,
       "to": _to,
       "price": price,
    }

    for instrument in instruments:
        # The factory returns a generator generating consecutive
        # requests to retrieve full history from date '_from' till '_to'
        df = pd.DataFrame()
        for r in InstrumentsCandlesFactory(instrument=instrument, params=params):
            data = client.request(r)
            results = [{"time": x['time'], "open": float(x['ask']['o']), "high": float(x['ask']['h']),
                        "low": float(x['ask']['l']), "close": float(x['ask']['c']), "volume": float(x['volume'])} for x in
                       data['candles']]
            if len(results) > 0:
                tmp_df = pd.DataFrame(results)
                df = df.append(tmp_df)
                print("last candle: " + df['time'].iloc[-1])


        print('writing: ' + './data/' + 'oanda' + instrument + '_' + granularity + '.csv')
        df.to_csv('./data/' + 'oanda' + instrument + '_' + granularity + '.csv', index=False)

