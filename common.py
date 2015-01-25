import pickle

class NameInfo:
    def __init__(self, height, tx_pos, txout_pos, tx_type, name, value):
        self.height = height
        self.tx_pos = tx_pos
        self.txout_pos = txout_pos
        self.tx_type = tx_type
        self.name = name
        self.value = value

    def __str__(self):
    	return "NameInfo({}, {}, {}, {})".format(self.height, self.tx_type, self.name, self.value)

    def __repr__(self):
    	return "NameInfo({}, {}, {}, {})".format(self.height, self.tx_type, self.name, self.value)

def load_object(filename):
    with open(filename, 'rb') as input:
        return pickle.load(input)

def save_object(obj, filename):
    with open(filename, 'wb') as output:
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)