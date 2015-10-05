__author__ = 'zohaib'
import inspect
from http import http_request
class A():
    def __init__(self):
        self.a = 10
        self.b = 20

    @classmethod
    def add(cls, c=0, d=0):
        return c - d

    @classmethod
    def add(cls, a=0, b=0):

        return a + b

    def show(self):
        http_request()


a = A()
print A.add(a=3, b=4)
