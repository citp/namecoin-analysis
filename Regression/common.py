#!/usr/bin/env python3

import pickle
import hashlib
import json
import psycopg2
import datetime
import csv
import tldextract
import subprocess
import threading
import re
import collections

from math import sqrt
import matplotlib


def latexify(fig_width=None, fig_height=None, columns=1):
    """Set up matplotlib's RC params for LaTeX plotting.
    Call this before plotting a figure.

    Parameters
    ----------
    fig_width : float, optional, inches
    fig_height : float,  optional, inches
    columns : {1, 2}
    """

    # code adapted from http://www.scipy.org/Cookbook/Matplotlib/LaTeX_Examples

    # Width and max height in inches for IEEE journals taken from
    # computer.org/cms/Computer.org/Journal%20templates/transactions_art_guide.pdf

    assert(columns in [1,2])

    if fig_width is None:
        fig_width = 3.39 if columns==1 else 6.9 # width in inches

    if fig_height is None:
        golden_mean = (sqrt(5)-1.0)/2.0    # Aesthetic ratio
        fig_height = fig_width*golden_mean # height in inches

    MAX_HEIGHT_INCHES = 8.0
    if fig_height > MAX_HEIGHT_INCHES:
        print("WARNING: fig_height too large:" + fig_height + 
              "so will reduce to" + MAX_HEIGHT_INCHES + "inches.")
        fig_height = MAX_HEIGHT_INCHES

    params = {'backend': 'ps',
              # 'text.latex.preamble': ['\usepackage{gensymb}'],
              'xtick.labelsize': 8,
              'ytick.labelsize': 8,
              'text.usetex': True,
              'figure.figsize': [fig_width,fig_height],
              'font.family': 'serif'
    }

    matplotlib.rcParams.update(params)


def format_axes(ax):

    for spine in ['top', 'right']:
        ax.spines[spine].set_visible(False)

    for spine in ['left', 'bottom']:
        ax.spines[spine].set_color(SPINE_COLOR)
        ax.spines[spine].set_linewidth(0.5)

    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_tick_params(direction='out', color=SPINE_COLOR)

    return ax

def is_valid_hostname(hostname):
    if len(hostname) > 255:
        return False
    if hostname.endswith("."): # A single trailing dot is legal
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    disallowed = re.compile("[^A-Z\d-]", re.IGNORECASE)
    splitName = hostname.split(".")
    if len(splitName) <= 1:
        return False

    if not tldextract.extract(hostname).suffix:
        return False

    return all( # Split by labels and verify individually
        (label and len(label) <= 63 # length is within proper range
         and not label.startswith("-") and not label.endswith("-") # no bordering hyphens
         and not disallowed.search(label)) # contains only legal characters
        for label in splitName)

def valuesOverN(counter, threshold):
    for (value, count) in counter.most_common():
        if count >= threshold:
            yield (value, count)
        else:
            break

def getTopValues(valueCounts, threshold):
    for w in sorted(valueCounts, key=valueCounts.get, reverse=True):
        yield w, valueCounts[w]
        if valueCounts[w] < threshold:
            break

def getDictSubset(nameDict, conditionFunc):
    return { key:value for key, value in nameDict.items() if conditionFunc(value) }

def alexaRanks():
    dotBitAlexa = collections.defaultdict(int)
    failedDomains = []
    with open('top-1m.csv', 'r') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            rank = int(row[0])
            url = row[1]
            try:
                parsed_url = tldextract.extract(url)
                bitDomain = "d/" + parsed_url.domain.lower()
                if bitDomain not in dotBitAlexa:
                    dotBitAlexa[bitDomain] = rank
            except UnicodeError:
                failedDomains.append(url)
    return dotBitAlexa

def blockTimeDict():
    conn = psycopg2.connect("dbname=abe user=postgres")
    cur = conn.cursor()
    cur.execute("SELECT block_height, block_ntime FROM block")
    res = cur.fetchall()
    return {row[0]: datetime.datetime.fromtimestamp(row[1]) for row in res}

class TransactionOutput(object):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id):
        self.height = height
        self.tx_pos = tx_pos
        self.txout_pos = txout_pos
        self.from_pub_id = from_pub_id
        self.to_pub_id = to_pub_id

    def expirationHeight(self):
        if self.height < 24000:
            return self.height + 12000
        if self.height < 48000:
            return 2 * self.height - 12000
        return self.height + 36000

    def isNew(self):
        return False

    def isFirstUpdate(self):
        return False

    def isUpdate(self):
        return False

    def hasValue(self):
        return False

class NameNew(TransactionOutput):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, tx_hash):
        super(NameNew, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id)
        self.tx_hash = tx_hash

    def __str__(self):
        return "NameNew({}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id)

    def isNew(self):
        return True

class NameUpdate(TransactionOutput):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, value):
        super(NameUpdate, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id)
        self.name = name
        self.value = value

    def __str__(self):
        return "NameUpdate({}, {}, {}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id, self.name, self.value)

    def hasValue(self):
        return True

    def isUpdate(self):
        return True

    def jsonValue(self):
        try:
            json_object = json.loads(self.value)
        except ValueError:
            return None
        return json_object

    def jsonDict(self):
        json_object = self.jsonValue()
        if json_object and isinstance(json_object, dict):
            return json_object
        return None

    def namespace(self):
        splitName = self.name.split('/')
        if len(splitName) > 1:
            return splitName[0]
        else:
            return None

    def nameWithoutNamespace(self):
        return self.name[(len(self.namespace()) + 1):]



class NameFirstUpdate(NameUpdate):
    def __init__(self, height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, tx_rand, value, tx_hash):
        super(NameFirstUpdate, self).__init__(height, tx_pos, txout_pos, from_pub_id, to_pub_id, name, value)
        self.tx_rand = tx_rand
        self.tx_hash = tx_hash

    def __str__(self):
        return "NameFirstUpdate({}, {}, {}, {}, {}, {})".format(self.height, self.tx_pos, self.from_pub_id, self.to_pub_id, self.name, self.value)

    def isUpdate(self):
        return False

    def isFirstUpdate(self):
        return True

class NameSession(object):
    def __init__(self, opList):
        self.ops = opList
        self.startHeight = self.ops[1].height
        self.endHeight = self.ops[-1].expirationHeight()

    @property
    def firstUpdate(self):
        return self.ops[1]
    
    @property
    def new(self):
        return self.ops[1]
        
    @property
    def lastUpdate(self):
        return self.ops[-1]

    def valueOps(self):
        return [op for op in self.ops if op.hasValue()]

    def valueChangingOps(self):
        prevValue = None
        for op in self.valueOps():
            if prevValue and prevValue != op.value:
                yield op
            prevValue = op.value

    def numberOfValueChanges(self):
        changeUpdates = 0
        lastValue = None
        for op in self.valueOps():
            if lastValue and op.value != lastValue:
                changeUpdates += 1
            lastValue = op.value
        return changeUpdates

    def numberOfOwnerChanges(self):
        ownerChanges = 0
        lastOwner = None
        for op in self.ops:
            if lastOwner and op.to_pub_id == lastOwner:
                ownerChanges += 1
            lastOwner = op.to_pub_id
        return ownerChanges

    def opAtHeight(self, height):
        if height < self.startHeight or height > self.endHeight:
            return None

        for op in self.valueOps():
            if op.height > height:
                break
            prevOp = op

        return prevOp

    def popOpAtHeight(self, height):
        if height < self.startHeight or height > self.endHeight:
            return None

        for op in self.valueOps():
            if op.height > height:
                break
            prevOp = op

        self.ops = [op for op in self.ops if op.height >= prevOp.height]

        return prevOp

class NameRecord(object):
    
    def __init__(self, opList):
        self.sessions = []
        sessionList = []
        for op in opList:
            if op.isNew():
                if sessionList:
                    self.sessions.append(NameSession(sessionList))
                sessionList = []
            sessionList.append(op)
        self.sessions.append(NameSession(sessionList))          

    def name(self):
        return self.latestOp().name

    def namespace(self):
        splitName = self.name().split('/')
        if len(splitName) > 1:
            return splitName[0]
        else:
            return None

    def domainName(self):
        if self.namespace() != "d":
            return None
        return self.name()[2:] + ".bit"

    def allOps(self):
        return [op for session in sessions for op in self.session.ops]

    def valueOps(self):
        return [op for session in sessions for op in self.session.valueOps()]

    def latestOp(self):
        return self.sessions[-1].ops[-1]

    def latestValue(self):
        return self.latestOp().value

    def latestValueJson(self):
        return self.latestOp().jsonValue()

    def latestValueJsonDict(self):
        return self.latestOp().jsonDict()

    def numberOfValueChanges(self):
        return sum([session.numberOfValueChanges() for session in self.sessions])

    def fractionRegistered(self, highest_block):
        """Calculate and return the fraction of time (in blocks) this name has been registered"""
        total_blocks = 0
        for session in self.sessions:
            total_blocks += min(session.endHeight, highest_block) - session.startHeight
        return total_blocks / highest_block

    
    def totalBlocksActive(self):
        totalActive = 0

    def reregistrationGap(self, maxHeight):
        gap = 0
        numGaps = 0
        for (i, session) in enumerate(self.sessions[:-1]):
            gap += self.sessions[i + 1].startHeight - session.endHeight
            numGaps += 1

        if self.sessions[-1].endHeight < maxHeight:
            gap += maxHeight - self.sessions[-1].endHeight
            numGaps += 1

        if numGaps > 0:
            return gap / numGaps
        else:
            return 0

    def popOpAtHeight(self, height):
        op = None
        sessionsToRemove = []
        for session in self.sessions:
            if session.startHeight > height:
                break
                
            value = session.popOpAtHeight(height)
            if value:
                op = value
                break
            else:
                sessionsToRemove.append(session)

        for session in sessionsToRemove:
            self.sessions.remove(session)

        return op

    def opAtHeight(self, height):
        for session in self.sessions:
            value = session.opAtHeight(height)
            if value: return value
        return None

    def isValidAtHeight(self, currentHeight):
        lastUpdateHeight = self.latestOp().height
        return self.latestOp().expirationHeight() >= currentHeight

def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input, encoding='ISO-8859-1')

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)

def ripemd160(data):
    return hashlib.new("ripemd160", data)

def hash160(data):
    """A standard compound hash."""
    return ripemd160(hashlib.sha256(data).digest()).digest()

class Pinger(object):
    status = {'alive': [], 'dead': []} # Populated while we are running
    hosts = [] # List of all hosts/ips in our input queue

    # How many ping process at the time.
    thread_count = 4

    # Lock object to keep track the threads in loops, where it can potentially be race conditions.
    lock = threading.Lock()

    def ping(self, ip):
        # Use the system ping command with count of 1 and wait time of 1.
        ret = subprocess.call(['ping', '-c', '1', '-W', '1', ip],
                              stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))

        return ret == 0 # Return True if our ping command succeeds

    def pop_queue(self):
        ip = None

        self.lock.acquire() # Grab or wait+grab the lock.

        if self.hosts:
            ip = self.hosts.pop()

        self.lock.release() # Release the lock, so another thread could grab it.

        return ip

    def dequeue(self):
        while True:
            ip = self.pop_queue()

            if not ip:
                return None

            result = 'alive' if self.ping(ip) else 'dead'
            self.status[result].append(ip)

    def start(self):
        threads = []

        for i in range(self.thread_count):
            # Create self.thread_count number of threads that together will
            # cooperate removing every ip in the list. Each thread will do the
            # job as fast as it can.
            t = threading.Thread(target=self.dequeue)
            t.start()
            threads.append(t)

        # Wait until all the threads are done. .join() is blocking.
        [ t.join() for t in threads ]

        return self.status
