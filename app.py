from flask import Flask, request, render_template
from flask_mail import Mail, Message
import json
import os
import mysql.connector
from dotenv import load_dotenv

dotenv_path = './.env'
load_dotenv(dotenv_path)

app = Flask (__name__)
app.debug = True

#Mailer setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'alertas.citi@gmail.com'
app.config['MAIL_PASSWORD'] = 'alertasCITI'
app.config['MAIL_DEFAULT_SENDER'] = 'alertas.citi@gmail.com'
mail = Mail(app)

@app.route('/', methods=['GET', 'POST'])
def hello():
  cnx = connection()
  cursor = cnx.cursor()

  #Get all rows
  query="SELECT protocol, ipsource, ipdest, message FROM logAlert ORDER BY timeStamp Desc"
  cursor.execute(query)
  rs = cursor.fetchall()

  #Get row count of last 24 hours
  query="SELECT count(*) FROM logAlert WHERE timeStamp>DATE_SUB(NOW(),INTERVAL 1 DAY);"
  cursor.execute(query)
  rowcount = cursor.fetchone()

  typeCount = []

  #Count per type
  query="SELECT count(*) FROM logAlert;"
  cursor.execute(query)
  allRows = cursor.fetchone()[0]

  query="SELECT count(*) FROM logAlert WHERE protocol='TCP';"
  cursor.execute(query)
  typeCount.append((1.0*cursor.fetchone()[0]/allRows)*100)

  query="SELECT count(*) FROM logAlert WHERE protocol='ICMP';"
  cursor.execute(query)
  typeCount.append((1.0*cursor.fetchone()[0]/allRows)*100)

  query="SELECT count(*) FROM logAlert WHERE protocol='UDP';"
  cursor.execute(query)
  typeCount.append((1.0*cursor.fetchone()[0]/allRows)*100)

  query="SELECT count(*) FROM logAlert WHERE protocol='IP';"
  cursor.execute(query)
  typeCount.append((1.0*cursor.fetchone()[0]/allRows)*100)

  json_type = json.dumps(typeCount)

  #Timestamps
  timestamps = []

  query="SELECT date_format(timeStamp, '%m/%d/%Y %l:%i %p') time FROM logAlert ORDER BY timeStamp Desc"
  cursor.execute(query)
  time = cursor.fetchone()
  while time is not None:
    timestamps.append(str(time[0]))
    time = cursor.fetchone()
  
  timestamps = json.dumps(timestamps)

  #SID Links
  query="SELECT sid FROM logAlert ORDER BY timeStamp Desc"
  cursor.execute(query)
  links = cursor.fetchall()
  links = json.dumps(links)

  #Count by message
  query="SELECT message,count(message) FROM logAlert GROUP BY message LIMIT 5"
  cursor.execute(query)
  topalerts = cursor.fetchall()

  cursor.close()
  cnx.close()

  return render_template('index.html', rs=rs, rowcount=rowcount, json_type=json_type, timestamps=timestamps, links=links, topalerts=topalerts)
  
def connection():
  #DB Connection
  USER = os.environ['MYSQLUSER']
  HOST = os.environ['MYSQLHOST']
  PASS = os.environ['MYSQLPASS']
  DB = os.environ['MYSQLDB']
  
  cnx = mysql.connector.connect(user=USER, database=DB, host=HOST, password=PASS)

  return cnx

@app.route('/db', methods=['POST'])
def add():
  cnx = connection()
  cursor = cnx.cursor()

  #JSON data
  j = request.get_json()
  j = j['data']  
  data = []

  #Iteration of json
  for i in j:
    t = (i['ipSource'], i['ipDest'], i['sid'], i['message'], i['protocol'])
    data.append(t)
  
  #DB insertion
  query = "INSERT INTO logAlert (ipsource, ipdest, sid, message, protocol) VALUES (%s,%s,%s,%s,%s)"
  cursor.executemany(query, data)
  cnx.commit()
  
  #DB Close
  cursor.close()
  cnx.close()
  
  return json.dumps({ 'msg':'success' })

@app.route('/mail', methods=['POST'])
def alert():
  #Mail Request Json
  j = request.get_json()
  j = j['data']
  data = "Las siguientes alertas se detectaron:\n"

  #Iteration of json
  for i in j:
    data += i['message'] + '\n'

  #Mail
  msg = Message (subject='Alerta', 
                 body=data, 
                 recipients=['eugenio_rangel@hotmail.com'])
  mail.send(msg)
  
  return json.dumps({ 'msg':'success' })

if __name__ == "__main__":
  app.run()


