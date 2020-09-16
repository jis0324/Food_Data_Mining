import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from configparser import ConfigParser
import os
import traceback
import json

app = Flask(__name__)
cursor = None
base_dir = os.path.dirname(os.path.abspath(__file__))

@app.route('/', methods=['GET', 'POST'])
def index():
  if request.method == "GET":
    lastest_date = ''
    select_Query = "select * from catalogues where excludeYN = False"
    cursor.execute(select_Query)
    catalogues_records = cursor.fetchall()

    if bool(catalogues_records):
      select_latest_date = "select max(modifiedDate) from catalogues"
      cursor.execute(select_latest_date)
      lastest_date = cursor.fetchone()

    if lastest_date:
      lastest_date = lastest_date[0].strftime('%m/%d/%Y')

    return render_template("index.html", data=catalogues_records, last_crawling_date=lastest_date)

  if request.method == "POST":
    return 'return data'

@app.route('/get_excluded_products', methods=['POST'])
def get_excluded_products():
  try:
    sql_update_query = """select * from catalogues where excludeYN = True"""
    cursor.execute(sql_update_query)
    excluded_records = cursor.fetchall()

    return_data = list()
    for row in excluded_records:
      row = list(row)
      row[21] = str(row[21])
      row[20] = str(row[20])
      return_data.append(row)
    return json.dumps(return_data)
  except:
    print(traceback.print_exc())
    return 'False'

@app.route('/get_unexcluded_products', methods=['POST'])
def get_unexcluded_products():
  try:
    sql_update_query = """select * from catalogues where excludeYN = False"""
    cursor.execute(sql_update_query)
    excluded_records = cursor.fetchall()

    return_data = list()
    for row in excluded_records:
      row = list(row)
      row[21] = str(row[21])
      row[20] = str(row[20])
      return_data.append(row)
    return json.dumps(return_data)
  except:
    print(traceback.print_exc())
    return 'False'

@app.route('/add_bookmark', methods=['POST'])
def add_bookmark():
  try:
    sql_update_query = """Update catalogues set bookmark = %s where uid = %s"""
    cursor.execute(sql_update_query, (True, request.json['uid']))
    cursor.execute("SELECT * FROM catalogues WHERE uid = %s", (request.json['uid'],))
    row = cursor.fetchone()
    row = list(row)
    row[21] = str(row[21])
    row[20] = str(row[20])
    return json.dumps(row)
  except:
    print(traceback.print_exc())
    return 'False'

@app.route('/remove_bookmark', methods=['POST'])
def remove_bookmark():
  try:
    sql_update_query = """Update catalogues set bookmark = %s where uid = %s"""
    cursor.execute(sql_update_query, (False, request.json['uid']))
    cursor.execute("SELECT * FROM catalogues WHERE uid = %s", (request.json['uid'],))
    row = cursor.fetchone()
    row = list(row)
    row[21] = str(row[21])
    row[20] = str(row[20])
    return json.dumps(row)
    return 'True'
  except:
    print(traceback.print_exc())
    return 'False'

@app.route('/add_exclude', methods=['POST'])
def add_exclude():
  try:
    sql_update_query = """Update catalogues set excludeYN = %s where uid = %s"""
    cursor.execute(sql_update_query, (True, request.json['uid']))

    return 'True'
  except:
    print(traceback.print_exc())
    return 'False'

@app.route('/remove_exclude', methods=['POST'])
def remove_exclude():
  try:
    sql_update_query = """Update catalogues set excludeYN = %s where uid = %s"""
    cursor.execute(sql_update_query, (False, request.json['uid']))

    return 'True'
  except:
    print(traceback.print_exc())
    return 'False'

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
    app.run(debug=True, host='0.0.0.0', port=80)
  else:
    raise Exception('Raised some erro in creating cursor object, Please try again.')