# -*- coding: utf-8 -*-
"""
Created on Sun Jan 28 17:04:24 2018

@author: Chris & Diana
"""

import sqlite3


darts_db = sqlite3.connect('data/darts_db.db')
cursor = darts_db.cursor()

def create_table():
    cursor.execute("ALTER TABLE player_stats ADD COLUMN top_score INTEGER")
    darts_db.commit()
    cursor.execute("CREATE TABLE IF NOT EXISTS player_stats(game_id TEXT, name TEXT, points INTEGER, turns INTEGER)")
def insert_data():
    cursor.execute("INSERT INTO checkout_table(value, checkout) VALUES (?, ?)", (43, '3 + D20'))
    darts_db.commit()

def alter_table():
    cursor.execute("ALTER TABLE player_stats ADD COLUMN score_hist VARCHAR(50)")
    darts_db.commit()


    
alter_table()

"""for i in range(len(values)):
    cursor.execute("INSERT INTO checkout_table(value, checkout) VALUES (?, ?)",(values[i], checkout[i]))
    darts_db.commit()"""
darts_db.commit()
#close connection
cursor.close()    
darts_db.close()