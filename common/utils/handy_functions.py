__author__ = 'erikfarmer'


import random
import string

def random_word(length):
    return ''.join(random.choice(string.lowercase) for i in xrange(length))
