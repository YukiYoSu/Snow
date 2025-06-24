import time

threat_level = 0
kraken_awake = False
last_message_time = time.time()

def increase_threat(amount):
    global threat_level, kraken_awake, last_message_time
    threat_level += amount
    last_message_time = time.time()
    if threat_level >= 100 and not kraken_awake:
        kraken_awake = True
        return True  # Kraken awakens
    return False

def get_threat_level():
    return threat_level

def decrease_threat(amount):
    global threat_level, kraken_awake
    if threat_level > 0:
        threat_level = max(threat_level - amount, 0)
    if threat_level == 0 and kraken_awake:
        kraken_awake = False
        return True  # Kraken falls asleep
    return False

def time_since_last_message():
    return time.time() - last_message_time
