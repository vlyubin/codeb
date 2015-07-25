import socket
import sys
import time
import datetime
import copy

from math import atan
import numpy as np
import socket
import sys
import time
import datetime
import copy
import random
  
sock = None

def linreg(X, Y):
    """
    return a,b in solution to y = ax + b such that root mean square distance between trend line and original points is minimized
    """
    N = len(X)
    Sx = Sy = Sxx = Syy = Sxy = 0.0
    for x, y in zip(X, Y):
        Sx = Sx + x
        Sy = Sy + y
        Sxx = Sxx + x*x
        Syy = Syy + y*y
        Sxy = Sxy + x*y
    det = Sxx * N - Sx * Sx
    return (Sxy * N - Sy * Sx)/det, (Sxx * Sy - Sx * Sxy)/det

def angle(x):
    x1,x2,n,m,b = 0.,len(x),11,2.,5.
    X = np.r_[x1:x2:n*1j]
    a,b = linreg(range(len(x)),x) #your x,y are switched from standard notation
    if a < -0.2:
        return 0
    else:
        return 1

sock = None

class Order:
  def __init__(self, price, shares):
    self.price = price
    self.shares = shares

ask_orders = {} # Map of asks for each stock STOCK_SYMBOL -> List[Bid]
bid_orders = {} # Map of bids for each stock STOCK_SYMBOL -> List[Bid]

net_worth = {}
cur_bids = []
dividend_ratio = {}
price_decrese = {}
last_purchase = None

def once_run(*commands):
  global sock
  HOST, PORT = "codebb.cloudapp.net", 17429
  
  data = OUR_USERNAME + " " + OUR_PASSWORD + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"
  return_lines = []

  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    sock.connect((HOST, PORT))
    
    sock.sendall(data)
    sfile = sock.makefile()
    rline = sfile.readline()
    while rline:
      return_lines.append(rline.strip())
      rline = sfile.readline()
  finally:
    sock.close()

  return return_lines

def run(commands):
  while True:
    try:
      data = once_run(commands)
      return data
    except KeyboardInterrupt:
      raise
    except:
      print "Warning: network failed"

OUR_USERNAME = "Team6"
OUR_PASSWORD = "bird"

securities = {}
orders = {}
my_cash = 0
my_securities = {}
my_orders = {}

# Query all the securities
def get_securities():
  inp = run("SECURITIES")[0].split()[1:]
  for i in range(len(inp)/4):
    securities[inp[4*i]] = (float(inp[4*i+1]), float(inp[4*i+2]), float(inp[4*i+3]))

def get_cash():
  global my_cash
  my_cash = float(run("MY_CASH")[0].split()[1])

def get_my_securities():
  global my_securities
  my_securities = {}
  inp = run("MY_SECURITIES")[0].split()[1:]
  for i in range(len(inp)/3):
    my_securities[inp[3*i]] = (int(inp[3*i+1]), float(inp[3*i+2]))

def get_my_orders():
  global my_orders
  my_orders = {}
  inp = run("MY_ORDERS")[0].split()[1:]
  for i in range(len(inp)/4):
    my_orders[inp[4*i+1]] = (inp[4*i], float(inp[4*i+2]), float(inp[4*i+3]))

def get_orders(stock):
  inp = run("ORDERS " + stock)[0].split()[1:]
  out = []

  ask_orders[stock] = []
  bid_orders[stock] = []

  for i in range(len(inp)/4):
    out.append( (inp[4*i], inp[4*i+1], float(inp[4*i+2]), int(inp[4*i+3])) )
    if inp[4*i] == 'ASK':
      ask_orders[stock].append(Order(float(inp[4*i+2]), int(inp[4*i+3])))
    else:
      bid_orders[stock].append(Order(float(inp[4*i+2]), int(inp[4*i+3])))
  orders[stock] = out

# Max buy and min sell prices
def get_buy_and_sell_prices(order):
  cur_buy = 0
  cur_sell = 100000
  for bid_ask, name, price, nshare in order:
    if bid_ask == "BID":
      if price > cur_buy:
        cur_buy = price
    if bid_ask == "ASK":
      if price < cur_sell:
        cur_sell = price
  return (cur_buy, cur_sell)

def smart_sell_1_iter(stock):
  get_my_securities()
  get_orders(stock)
  this_ord = orders[stock]

  cur_buy, cur_sell = get_buy_and_sell_prices(this_ord)

  want_price = max(cur_buy - 0.005, cur_sell - price_decrese[stock])
  num_shares = int(my_securities[stock][0])
  price_decrese[stock] *= 1.2

  if num_shares <= 4:
    want_price = cur_buy - 0.005

  print "Selling %s: %d shares at %f" % (stock, num_shares, want_price)
  run("ASK %s %f %d"% (stock, want_price, num_shares))

def is_increasing_net_worth(sec):
  if len(net_worth[sec]) > 3:
    rv = angle(net_worth[sec])
  else:
    rv = 0
  return rv

def pick_stock():
  global cur_bids
  for sec,_ in securities.iteritems():
    get_orders(sec)

  magic_nums = []
  for sec,_ in securities.iteritems():
    differnce_in_ask_bid = abs(ask_orders[sec][0].price - bid_orders[sec][-1].price) / ask_orders[sec][0].price
    is_net_worth_inc = is_increasing_net_worth(sec)

    print sec, is_net_worth_inc, differnce_in_ask_bid
    magic_nums.append((-1000000 * is_net_worth_inc + 100 * differnce_in_ask_bid, sec))

  magic_nums = sorted(magic_nums)
  # cannot buy until 4 minutes after selling it

  increase_premium = False
  buy_market = False
  if datetime.datetime.now() - last_purchase > datetime.timedelta(seconds=10):
    increase_premium = True
  if datetime.datetime.now() - last_purchase > datetime.timedelta(seconds=30):
    buy_market = True

  attempts = 0
  for v,sec in magic_nums:
    if attempts > 3:
      break

    bad = False
    if sec in time_sold and datetime.datetime.now() - time_sold[sec] < datetime.timedelta(minutes=2):
      # if we just sold this less than 2 minutes ago
      bad = True
    if sec in my_securities and my_securities[sec][0] > 0 and sec in time_bought and datetime.datetime.now() - time_bought[sec] < datetime.timedelta(seconds=3):
      # if we already have this stock
      bad = True
    if not bad:
      get_orders(sec)
      cur_buy, cur_sell = get_buy_and_sell_prices(orders[sec])

      if buy_market:
        buying_price = min(cur_sell, cur_buy) + 0.001
      elif increase_premium:
          buying_price = min(cur_sell, cur_buy) + 0.5
      else:
        buying_price = max(cur_sell, cur_buy) + 0.001
      num_shares = int(my_cash / buying_price)

      if num_shares < 2:
        break

      print "Trying to buy %s: %d shares at %f" % (sec, num_shares, buying_price)
      run("BID %s %f %d" % (sec, buying_price, num_shares))
      cur_bids.append(sec)
      attempts += 1

time_bought = {}
time_sold = {}
def trade():
  global cur_bids
  global last_purchase
  for i in xrange(4):
    once_run("")

  get_cash()
  old_cash = my_cash
  previous_securities = my_securities
  last_purchase = datetime.datetime.now()

  while True:
    get_securities()

    for sec in securities:
      if sec not in net_worth:
        net_worth[sec] = []
      net_worth[sec].append(securities[sec][0])
      net_worth[sec] = net_worth[sec][-5:]

      if sec not in dividend_ratio:
        dividend_ratio[sec] = securities[sec][1]

    for sec in cur_bids:
      run("CLEAR_BID %s" % (security))
    cur_bids = []

    old_cash = my_cash
    get_cash()

    get_my_securities()
    for security in my_securities:
      if my_securities[security][0] > previous_securities[security][0] and previous_securities[security][0] == 0:
        print 'BOUGHT ' + security + ' ' + str(my_securities[security][0])
        time_bought[security] = datetime.datetime.now()
        price_decrese[security] = 0.05
        last_purchase = datetime.datetime.now()
    previous_securities = my_securities

    print "MY CASH:", my_cash

    num_owned = 0
    for sec, vl in my_securities.iteritems():
      if vl[0] > 0:
        num_owned += 1

    # If we don't have any stocks, buy some
    if my_cash > 320 and num_owned < 4:
      pick_stock()

    not_making_money = False
    if my_cash > old_cash and my_cash - old_cash < 1 and my_cash - old_cash > 0.0000001:
      not_making_money = True

    # If we hold a stock for more than 25 seconds, start smart selling
    for sec, vl in my_securities.iteritems():
      we_hold = vl[0]
      if we_hold > 0:
        if (sec in time_bought and datetime.datetime.now() - time_bought[sec] > datetime.timedelta(seconds=25)) or not_making_money:
          smart_sell_1_iter(sec)
          # If we managed to sell something completely, update it
          time_sold[sec] = datetime.datetime.now()
    time.sleep(1)

get_my_securities()
for security in my_securities:
  price_decrese[security] = 0.05
  time_bought[security] = datetime.datetime.now() - datetime.timedelta(seconds=90)

trade()
