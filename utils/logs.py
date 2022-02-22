import pickle

PROTOCOL_VERSION = 3
LOGS_DIR = "logs/"

def load(path):
    file = open(LOGS_DIR + path,'rb')
    logs = pickle.load(file, fix_imports = True) 
    file.close()
    return logs

def dump(path, logs):
    file = open(LOGS_DIR + path,'wb')
    pickle.dump(logs, file, protocol = PROTOCOL_VERSION, fix_imports = True) 
    file.close()