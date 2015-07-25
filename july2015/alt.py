import socket
import sys
import time
import datetime
import copy
  
sock = None

class Order:
  def __init__(self, price, shares):
    self.price = price
    self.shares = shares

ask_orders = {} # Map of asks for each stock STOCK_SYMBOL -> List[Bid]
bid_orders = {} # Map of bids for each stock STOCK_SYMBOL -> List[Bid]

def once_run(*commands):
  global sock
  HOST, PORT = "codebb.cloudapp.net", 17429
  
  data = OUR_USERNAME + " " + OUR_PASSWORD + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"
  return_lines = []

  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #print socket.gettimeout()
    sock.settimeout(3)

    sock.connect((HOST, PORT))
    sock.sendall(data)
    sfile = sock.makefile()
    rline = sfile.readline()
    while rline:
      #print(rline.strip())
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

def subscribe():
  HOST, PORT = "codebb.cloudapp.net", 17429
  
  data=OUR_USERNAME + " " + OUR_PASSWORD + "\nSUBSCRIBE\n"

  try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.connect((HOST, PORT))
    sock.sendall(data)
    sfile = sock.makefile()
    rline = sfile.readline()
    while rline:
      print(rline.strip())
      rline = sfile.readline()
  finally:
    sock.close()


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
  cur_sell = 1000
  for bid_ask, name, price, nshare in order:
    if bid_ask == "BID":
      if price > cur_buy:
        cur_buy = price
    if bid_ask == "ASK":
      if price < cur_sell:
        cur_sell = price
  return (cur_buy, cur_sell)

def sell_stock(stock):
  """
  Dump everything instantly (don't do this lol)

  while we still have stock:
    get highest buyer
    ask that much
  """
  time_sold[stock] = datetime.datetime.now()
  while True:
    get_my_securities()
    get_orders(stock)
    this_ord = orders[stock]

    cur_buy, cur_sell = get_buy_and_sell_prices(this_ord)

    # assume we can sell at cur_buy
    selling_price = cur_buy - 0.1
    num_shares = int(my_securities[stock][0])

    if num_shares == 0:
      break

    print "Selling %s: %d shares at %f" % (stock, num_shares, selling_price)
    run("ASK %s %f %d"% (stock, selling_price, num_shares))

def smart_sell_1_iter(stock):
  get_my_securities()
  get_orders(stock)
  this_ord = orders[stock]

  cur_buy, cur_sell = get_buy_and_sell_prices(this_ord)
  want_price = max(cur_buy - 0.01, cur_sell - 0.06)

  num_shares = int(my_securities[stock][0])
  print "Selling %s: %d shares at %f" % (stock, num_shares, want_price)
  run("ASK %s %f %d"% (stock, want_price, num_shares))

def smart_sell(stock):
  while True:
    smart_sell_1_iter(stock)
    time.sleep(3)

def pick_stock():
  for sec,_ in securities.iteritems():
    get_orders(sec)

  magic_nums = []
  for sec,_ in securities.iteritems():
    diff = abs(ask_orders[sec][0].price - bid_orders[sec][-1].price)
    magic_nums.append((diff / bid_orders[sec][-1].price, sec))

  magic_nums = sorted(magic_nums)
  # cannot buy until 4 minutes after selling it
  for v,sec in magic_nums:
    bad = False
    if sec in time_sold and datetime.datetime.now() - time_sold[sec] < datetime.timedelta(minutes=2):
      # if we just sold this less than 2 minutes ago
      bad = True
    if sec in my_securities and my_securities[sec][0] > 0 and datetime.datetime.now() - time_bought[sec] < datetime.timedelta(seconds=3):
      # if we already have this stock
      bad = True
    if not bad:
      get_orders(sec)
      cur_buy, cur_sell = get_buy_and_sell_prices(orders[sec])

      buying_price = cur_buy + 0.005
      num_shares = int(my_cash / buying_price)

      if num_shares < 2:
        break

      print "Trying to buy %s: %d shares at %f" % (sec, num_shares, buying_price)
      run("BID %s %f %d" % (sec, buying_price, num_shares))

time_bought = {}
time_sold = {}
def autorun():
  while True:
    get_securities()

    for security in securities:
      run("CLEAR_BID %s" % (security))

    get_cash()

    previous_securities = my_securities
    get_my_securities()
    for security in my_securities:
      if (not security in previous_securities) or (my_securities[security][0] > previous_securities[security][0]):
        time_bought[security] = datetime.datetime.now()

    print "MY CASH:", my_cash

    num_owned = 0
    for sec, vl in my_securities.iteritems():
      if vl[0] > 0:
        num_owned += 1

    # If we don't have any stocks, buy some
    if my_cash > 320 and num_owned < 4:
      pick_stock()

    # If we hold a stock for more than 30 seconds, start smart selling
    for sec, vl in my_securities.iteritems():
      we_hold = vl[0]
      if we_hold > 0:
        if datetime.datetime.now() - time_bought[sec] > datetime.timedelta(seconds=30):
          smart_sell_1_iter(sec)
          # If we managed to sell something completely, update it
          time_sold[sec] = datetime.datetime.now()
    time.sleep(1)

def sell_all():
  get_my_securities()
  for security in my_securities:
    sell_stock(security)

sell_all()
autorun()
