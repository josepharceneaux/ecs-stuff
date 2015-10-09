__author__ = 'erikfarmer'


import random
import string

def randomword(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))
