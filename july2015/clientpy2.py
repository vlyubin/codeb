import socket
import sys
import time
import datetime
import copy

# Default stuff

sock = None
cur_time = 0

def once_run(*commands):
  global sock
  HOST, PORT = "codebb.cloudapp.net", 17429
  
  data=OUR_USERNAME + " " + OUR_PASSWORD + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"
  return_lines = []

  while True:
    one_more = 0
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
    except Exception:
      one_more = 1
    finally:
      sock.close()
    if one_more == 0:
      break

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

# Magic constants

class Security:
  def __init__(self, net_worth, dividend_ratio, volatility):
    self.net_worth = net_worth
    self.dividend_ratio = dividend_ratio
    self.volatility = volatility

class MySecurity:
  def __init__(self, shares, dividend_ratio):
    self.shares = shares
    self.dividend_ratio = dividend_ratio

class Order:
  def __init__(self, price, shares):
    self.price = price
    self.shares = shares

securities = {}
my_cash = 0
last_cash_gain = 100
my_securities = {}
my_orders = {}

ask_orders = {} # Map of asks for each stock STOCK_SYMBOL -> List[Bid]
bid_orders = {} # Map of bids for each stock STOCK_SYMBOL -> List[Bid]

hold_time = {}

# Helper functions

def get_securities():
  inp = run("SECURITIES")[0].split()[1:]
  for i in range(len(inp)/4):
    securities[inp[4*i]] = Security(float(inp[4*i+1]), float(inp[4*i+2]), float(inp[4*i+3]))

def get_cash():
  global my_cash
  my_cash = float(run("MY_CASH")[0].split()[1])

def get_my_securities():
  global my_securities
  my_securities = {}
  inp = run("MY_SECURITIES")[0].split()[1:]
  for i in range(len(inp)/3):
    my_securities[inp[3*i]] = MySecurity(int(inp[3*i+1]), float(inp[3*i+2]))

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
    if inp[4*i] == 'ASK':
      ask_orders[stock].append(Order(float(inp[4*i+2]), int(inp[4*i+3])))
    else:
      bid_orders[stock].append(Order(float(inp[4*i+2]), int(inp[4*i+3])))

def buy():
  options = []
  for security in ask_orders:
    if len(bid_orders[security]) > 0 and len(ask_orders[security]) > 0:
      options.append((abs(ask_orders[security][0].price - bid_orders[security][-1].price), security))

  options.sort(key=lambda x: x[0])
  if len(options) > 0:
    security = options[0][1]
    price = ask_orders[security][0].price + 0.001
    count = ask_orders[security][0].shares
    count = min(count, int(my_cash / price))

    if count == 0:
      return

    once_run('CLEAR_BID')
    print 'Bidding ' + security + " for price " + str(price) + " ; num shares " + str(count)
    once_run("BID " + security + " " + str(price) + " " + str(count))

def sell_security(security):
  price = bid_orders[security][-1].price - 0.001
  count = bid_orders[security][-1].shares
  count = min(count, my_securities[security].shares)

  once_run('CLEAR_ASK')
  print 'Asking ' + security + " for price " + str(price) + " ; num shares " + str(count)
  once_run("ASK " + security + " " + str(price) + " " + str(count))

def sell():
  for security in securities:
    if not security in my_securities:
      hold_time[security] = 0

  for security in my_securities:
    hold_time[security] += 1

    print 'Checking ' + security
    if hold_time[security] > 20 or last_cash_gain < 1.0:
      # sell security
      sell_security(security)

def trade():
  global cur_time
  # Kill old connections
  for i in xrange(5):
    once_run("")

  get_securities()
  for k in securities:
    hold_time[k] = 0

  while True:
    old_cash = my_cash
    get_cash()
    last_cash_gain = my_cash - old_cash
    if last_cash_gain < 0:
      # We bought some stocks, set last_cash_gain to large numbre to avoid thinking that we should sell
      last_cash_gain = 1000

    get_securities()
    
    last_my_securities = my_securities
    get_my_securities()

    print "MY_CASH " + str(my_cash)    

    for k in securities:
        get_orders(k)

    #print "Cheapest ask:"
    #for security in ask_orders:
    #  ask_orders[security].sort(key=lambda x: x.price)
    #  if len(ask_orders[security]) != 0:
    #    print security + ": " + str(ask_orders[security][0].price) + " (count: " + str(ask_orders[security][0].shares) + ")"

    #print "Most expensive bid:"
    #for security in bid_orders:
    #  bid_orders[security].sort(key=lambda x: x.price)
    #  if len(bid_orders[security]) != 0:
    #    print security + ": " + str(bid_orders[security][-1].price) + " (count: " + str(bid_orders[security][-1].shares) + ")"

    # Check if we have wasted shares, if so sell them
    sell()

    get_cash()

    if my_cash > 10:
      # Buy the best shares available
      buy()

    time.sleep(1)
    cur_time += 1

trade()
