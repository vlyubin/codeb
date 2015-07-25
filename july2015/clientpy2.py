import socket
import sys
import time
import datetime
import copy

# Default stuff

sock = None

def once_run(*commands):
  global sock
  HOST, PORT = "codebb.cloudapp.net", 17429
  
  data=OUR_USERNAME + " " + OUR_PASSWORD + "\n" + "\n".join(commands) + "\nCLOSE_CONNECTION\n"
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
my_securities = {}
my_orders = {}

ask_orders = {} # Map of asks for each stock STOCK_SYMBOL -> List[Bid]
bid_orders = {} # Map of bids for each stock STOCK_SYMBOL -> List[Bid]

# Helper functions

def get_securities():
  inp = run("SECURITIES")[0].split()[1:]
  for i in range(len(inp)/4):
    securities[inp[4*i]] = Security(float(inp[4*i+1]), float(inp[4*i+2]), float(inp[4*i+3]))

def get_cash():
  global my_cash
  print run("MY_CASH")
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
  pass # TODO

def sell():
  pass # TODO

def trade():
  cur_time = 0
  # Kill old connections
  for i in xrange(5):
    once_run("")

  while True:
    get_cash()
    get_securities()
    get_my_securities()

    print "MY_CASH " + str(my_cash)    

    print "GEN_SEC:"
    for k in securities:
        get_orders(k)

    print "BEST_ASK:"
    for security in ask_orders:
      ask_orders[security].sort(key=lambda x: x.price)
      if len(ask_orders[security]) != 0:
        print security + ": " + str(ask_orders[security][-1].price) + " (count: " + str(ask_orders[security][-1].shares) + ")"

    print "BEST_BID:"
    for security in bid_orders:
      bid_orders[security].sort(key=lambda x: x.price)
      if len(bid_orders[security]) != 0:
        print security + ": " + str(bid_orders[security][0].price) + " (count: " + str(bid_orders[security][0].shares) + ")"

    # Check if we have wasted shares, if so sell them
    sell()

    get_cash()

    if my_cash > 100:
      # Buy the best shares available
      buy()

    time.sleep(1)
    cur_time += 1

trade()
