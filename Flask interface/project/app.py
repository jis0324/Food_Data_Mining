import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from configparser import ConfigParser
import os
import json
import time

app = Flask(__name__)
cursor = None
base_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == "GET":
    select_Query = "select * from catalogues"
    cursor.execute(select_Query)
    catalogues_records = cursor.fetchall()

    return render_template("index.html", data=catalogues_records)

  if request.method == "POST":
    return 'return data'

if __name__ == "__main__":
  # database connect
  parser = ConfigParser()   # create a parser

  parser.read("{}/config.ini".format(base_dir))    # read config file

  # get section, default to postgresql
  db_config = {}
  if parser.has_section("postgresql"):
    params = parser.items("postgresql")
    for param in params:
      db_config[param[0]] = param[1]
  else:
    raise Exception('Section {0} not found in the {1} file'.format("postgresql", "config.ini"))

  # connect to the PostgreSQL server
  conn = psycopg2.connect(**db_config)

  # Setting auto commit false
  conn.autocommit = True

  # Creating a cursor object using the cursor() method
  cursor = conn.cursor()

  if cursor:
    app.run(debug=True)
  else:
    raise Exception('Raised some erro in creating cursor object, Please try again.')