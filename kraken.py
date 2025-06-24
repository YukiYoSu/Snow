threat_level = 0

def increase_threat(amount):
    global threat_level
    threat_level += amount
    return threat_level >= 100

def get_threat_level():
    return threat_level
