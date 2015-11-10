__author__ = 'erikfarmer'


import random
import string

def random_word(length):
    # Creates a random lowercase string, usefull for testing data.
    return ''.join(random.choice(string.lowercase) for i in xrange(length))


def random_letter_digit_string(size=6, chars=string.lowercase + string.digits):
    # Creates a random string of lowercase/uppercase letter and digits. Useful for Oauth2 tokens.
    return ''.join(random.choice(chars) for _ in range(size))
