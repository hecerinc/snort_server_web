from flask import Flask
from flask import request
from flask_mail import Mail
from flask_mail import Message
import json
import mysql.connector

app = Flask (__name__)
#app.debug = True

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
  print(str(request.form))
  return 'hello'

@app.route('/db', methods=['POST'])
def add():
  #DB Connection
  cnx = mysql.connector.connect(user='hrincon_capture', database='hrincon_testcapture', host='192.185.71.147', password='capture')
  cursor = cnx.cursor()

  #JSON data
  j = json.loads(request.form['data'])
  data = (j['ipSource'], j['ipDest'], j['sid'], j['message'], j['protocol'])
  
  #DB insertion
  query = "INSERT INTO logAlert (ipsource, ipdest, sid, message, protocol) VALUES (%s,%s,%s,%s,%s)"
  cursor.execute(query, data)
  cnx.commit()
  
  #DB Close
  cursor.close()
  cnx.close()
  
  return json.dumps({ 'msg':'success' })

@app.route('/mail', methods=['POST'])
def alert():
  #Mail Request Json
  j = json.loads(request.form['data'])
  print j
  #Mail
  msg = Message (subject='Alerta', 
                 body=j['message'], 
                 recipients=['eugenio_rangel@hotmail.com'])
  mail.send(msg)
  
  return json.dumps({ 'msg':'success' })

if __name__ == "__main__":
  app.run()


