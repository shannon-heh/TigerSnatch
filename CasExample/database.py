#!/usr/bin/env python

#-----------------------------------------------------------------------
# database.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

from sqlite3 import connect
from sys import stderr
from os import path
from book import Book

#-----------------------------------------------------------------------

class Database:
    
    def __init__(self):
        self._connection = None

    def connect(self):      
        DATABASE_NAME = 'penny.sqlite'
        if not path.isfile(DATABASE_NAME):
            raise Exception('Database connection failed')
        self._connection = connect(DATABASE_NAME)
                    
    def disconnect(self):
        self._connection.close()

    def search(self, author):
        cursor = self._connection.cursor()

        QUERY_STRING = \
            'select author, title, price from books ' + \
            'where author like ?'
        cursor.execute(QUERY_STRING, (author+'%',)) 
        
        books = []
        row = cursor.fetchone()
        while row:  
            book = Book(str(row[0]), str(row[1]), float(row[2]))
            books.append(book);
            row = cursor.fetchone()
        cursor.close()
        return books

#-----------------------------------------------------------------------

# For testing:

if __name__ == '__main__':
    database = Database()
    database.connect()
    books = database.search('Kernighan')
    for book in books:
        print(book)
    database.disconnect()
