import csv
import sqlite3

con = sqlite3.connect("jarvis.db") #for connection to database
cursor = con.cursor() #variable to use in database to access database connection features

#query = "CREATE TABLE IF NOT EXISTS sys_command(id integer primary key, name VARCHAR(100), path VARCHAR(1000))"
#cursor.execute(query)

#query = "INSERT INTO sys_command VALUES (null,'onenote', 'C:\\Program Files\\Microsoft Office\\root\\Office16\\ONENOTE.EXE')"
#cursor.execute(query)
#con.commit()

#query = "CREATE TABLE IF NOT EXISTS web_command(id integer primary key, name VARCHAR(100), url VARCHAR(1000))"
#cursor.execute(query)

#query = "INSERT INTO web_command VALUES (null,'youtube', 'https://www.youtube.com/')"
#cursor.execute(query)
#con.commit()

#this command is used to delete the data from the web)commands table in database 
#query = "DELETE FROM sys_command WHERE name='youtube'"
#cursor.execute(query)
#con.commit()

# testing module
#app_name = "android studios"
#cursor.execute("SELECT path FROM sys_command WHERE name = ?", (app_name,))
#result = cursor.fetchone()
#print(result)

#cursor.execute('''CREATE TABLE IF NOT EXISTS contacts (id integer primary key, name VARCHAR(200), mobile_no VARCHAR(255), email VARCHAR(255) NULL)''')

# Specify the column indices you want to import (0-based index)
# Example: Importing the 1st and 3rd columns
#desired_columns_indices = [0, 18]

# Read data from CSV and insert into SQLite table for the desired columns
#with open('contacts.csv', 'r', encoding='utf-8') as csvfile:
#    csvreader = csv.reader(csvfile)
#    for row in csvreader:
#        selected_data = [row[i] for i in desired_columns_indices]
#        cursor.execute(''' INSERT INTO contacts (id, 'name', 'mobile_no') VALUES (null, ?, ?);''', tuple(selected_data))

# Commit changes and close connection
#con.commit()
#con.close()


# this is the code to insert a single contact value into the database
#query = "INSERT INTO contacts VALUES (null,'lekhaj', '1234567890', NULL)"
#cursor.execute(query)
#con.commit()

# this is the code to insert a single delete value into the database
#query = "DELETE FROM contacts WHERE name='lekhaj'"
#cursor.execute(query)
#con.commit()

#to fetch the contact number from the database
#query = 'Shiva'
#query = query.strip().lower()

#cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
#results = cursor.fetchall()
#print(results[0][0])