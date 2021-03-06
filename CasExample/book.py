#!/usr/bin/env python

#-----------------------------------------------------------------------
# book.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

class Book:

    def __init__(self, author, title, price):
        self._author = author
        self._title = title
        self._price = price

    def __str__(self):
        return self._author + ', ' + self._title + ', ' + \
           str(self._price)

    def getAuthor(self):
        return self._author

    def getTitle(self):
        return self._title

    def getPrice(self):
        return self._price
