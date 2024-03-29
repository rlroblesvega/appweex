from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, make_response, send_from_directory
from ApiSendBlue import sendMailOperationConfirm, sendMailResetPassword
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
from flask_mail import Mail
from cryptography.fernet import Fernet as frt
import json
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from copy import deepcopy
from datetime import datetime
from datetime import timedelta
import datetime
from flask_cors import CORS, cross_origin
import os
import uuid
import random
import string
import re

import weexConstants
import correoweex
from werkzeug.security import generate_password_hash, check_password_hash

import schedule
import time
import webscraping
from apscheduler.schedulers.background import BackgroundScheduler
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from array import array
from flask import abort 
from authlib.integrations.flask_client import OAuth

# RUTA LOCAL WINDOWS
# UPLOAD_FOLDER = os.path.abspath(".\\uploads\\")
# UPLOAD_FOLDER = os.path.abspath("uploads")
UPLOAD_FOLDER = os.path.abspath("./uploads")
# RUTA LOCAL WINDOWS
#UPLOAD_DNI = os.path.abspath(".\\uploads\\Personal\\")
#UPLOAD_DNI = os.path.abspath("uploadsPersonal")
UPLOAD_DNI = os.path.abspath("./uploads/Personal/")

#Instanciamos un objeto de tipo Mail
mail = Mail()  

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
            
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["UPLOAD_DNI"] = UPLOAD_DNI
# flask-login
login_manager = LoginManager()
login_manager.init_app(app)
#login_manager.login_view = "login"

## Mail
#mail = Mail(app)

## MySQL Connection
app.config['MYSQL_HOST'] = weexConstants.MYSQL_HOST
app.config['MYSQL_USER'] = weexConstants.MYSQL_USER
app.config['MYSQL_PASSWORD'] = weexConstants.MYSQL_PASSWORD
app.config['MYSQL_DB'] = weexConstants.MYSQL_DB
mysql = MySQL(app)

#settings secret key
app.secret_key = 'my$ecre7key'
app.permanent_session_lifetime = timedelta(minutes=8)

varPath1 = str(app.root_path)
varPath2 = app.instance_path
varPath3 = os.path.dirname(app.instance_path)

## Config values for upload image
# app.config["IMAGE_UPLOADS"] = "D:\\FREDDY\\Escritorio\\Trabajos\\We-Exchange\\flask\\we_ex_app\\static\\img\\uploads"

vardirf1 = str(r"" + varPath1   +  "") 

#os.path.dirname(r"static\img\uploads") 

vardirf2 = os.path.dirname(r"\static\img\uploads")
vardirf3 =  vardirf1 + vardirf2



app.config["IMAGE_UPLOADS"] =  vardirf3 

app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG", "GIF"]
app.config["MAX_IMAGE_FILESIZE"] = 500000 # 500 000 bytes

def allowed_image(filename):
    if not "." in filename:
        return False
    
    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else :
        return False

def allowed_image_filesize(filesize):
    if int(filesize) <= app.config["MAX_IMAGE_FILESIZE"]:
        return True
    else:
        return False

def ExisteCliente(correo):
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "'")
    data = cur.fetchall()
    cur.close()
    if(len(data) == 1):
        return True
    else:
        return False

def ObtenerRolByUser(username):
    cur = mysql.connection.cursor() 
    cur.execute("SELECT ROLE_ID FROM m_cliente WHERE CORREO_ELECTRONICO = '" + username + "'")
    data = cur.fetchall()
    cur.close()
    return data[0][0]

def ExisteOrden(codorden):
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM m_orden WHERE CODORDEN = '" + codorden + "'")
    data = cur.fetchall()
    cur.close()
    if(len(data) == 1):
        return True
    else:
        return False


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
    
""" @app.route('/prueba') """
def TraerTipoCambioDolarSimulacion():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COMPRA, VENTA FROM tasa_cambio WHERE IDMONEDA_1 = 2 ORDER BY FECHAHORAACTUALIZACION DESC LIMIT 1")
    data = cur.fetchall()
    dataTC = data[0]
    cur.close()
    return dataTC

@app.route('/weex/tasa-cambio/v1', methods=['GET'])
def apiTipoCambioMonedas():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COMPRA, VENTA FROM tasa_cambio WHERE IDMONEDA_1 = 2 ORDER BY FECHAHORAACTUALIZACION DESC LIMIT 1")
    data = cur.fetchall()
    #print(data[0][0])
    #print(data[0][1])
    cur.close()
    result = {
        'ratesBD': {
                'compra': data[0][0],
                'venta': data[0][1]
            }
        }

    ##
    return jsonify(result)

@app.route('/weex/tasa-cambioCompra/v1/<moneda>', methods=['GET'])
@cross_origin()
def apiTipoCambioMonedashome(moneda):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COMPRA, VENTA FROM tasa_cambio WHERE IDMONEDA_1 = 2 ORDER BY FECHAHORAACTUALIZACION DESC LIMIT 1")
    data = cur.fetchall()
    equivalenteUSD = 1 / data[0][1]
    equivalentePEN = data[0][0]
    cur.close()
    
    if (moneda == 'PEN'):
        result = {
            'rates': {
                'USD': equivalenteUSD,
                'PEN': 1
                }
            }

    if (moneda == 'USD'):
        result = {
            'rates': {
                'USD': 1,
                'PEN': equivalentePEN
                }
            }

    return jsonify(result)

@app.route('/weex/tasa-cambioVenta/v1/<moneda>', methods=['GET'])
@cross_origin()
def apiTipoCambioMonedashome2(moneda):
    cur = mysql.connection.cursor()
    cur.execute("SELECT COMPRA, VENTA FROM tasa_cambio WHERE IDMONEDA_1 = 2 ORDER BY FECHAHORAACTUALIZACION DESC LIMIT 1")
    data = cur.fetchall()
    equivalenteUSD = 1 / data[0][0]
    equivalentePEN = data[0][1]
    cur.close()
    
    if (moneda == 'PEN'):
        result = {
            'rates': {
                'USD': equivalenteUSD,
                'PEN': 1
                }
            }

    if (moneda == 'USD'):
        result = {
            'rates': {
                'USD': 1,
                'PEN': equivalentePEN
                }
            }

    return jsonify(result)

@app.route('/weex/actualizar/tasa-cambio/v1', methods=['POST'])
def updateTipoCambioInvesting():
    requestBody = request.get_json(force=True)
    params = {
        "id": requestBody['id'],
        "compra": requestBody['compra'],
        "venta": requestBody['venta']
    }
    #print(params)
    query = "UPDATE tasa_cambio SET COMPRA = {data[compra]}, VENTA = {data[venta]} WHERE ID = {data[id]}"
    query = query.format(data=params)
    
    cur = mysql.connection.cursor()
    cur.execute(query)
    mysql.connection.commit()
    result = {
        'response': {
            'code': '000',
            'message': 'Se actualizó el tipo de cambio correctamente'
        }
    }
    return jsonify(result)

def TraerDataBancoDeDondeEnvias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT IDBANCO, NOMBRE, DESCRIPCION FROM de_banco")
    data = cur.fetchall()
    dataBanco = data
    cur.close()
    return dataBanco

def TraerDataTipDoc():
    cur = mysql.connection.cursor()
    cur.execute("SELECT ID, DESCRIPCION FROM de_tipo_documento")
    data = cur.fetchall()
    dataTipDoc = data
    cur.close()
    return dataTipDoc

def TraerDataBanco():
    cur = mysql.connection.cursor()
    cur.execute("SELECT IDBANCO, NOMBRE, DESCRIPCION FROM de_banco")
    data = cur.fetchall()
    dataBanco = data
    cur.close()
    return dataBanco

def ObtenerIdMoneda(codigoMoneda):
    cur = mysql.connection.cursor()
    cur.execute("SELECT IDMONEDA from de_moneda WHERE CODIGO = '" + codigoMoneda + "'")
    data = cur.fetchall()
    dataIdMoneda = data
    cur.close()
    return dataIdMoneda

def TraerDataCuentas(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT C.IDCUENTA, B.NOMBRE , C.NUMERO_CUENTA, C.NOMBRE_TITULAR, REPLACE (REPLACE(C.IDMONEDA, 1, 'SOLES'), 2, 'DOLARES') FROM m_cuenta C INNER JOIN de_banco B ON C.IDBANCO = B.IDBANCO  WHERE IDCLIENTE = '" + id + "'")
    data = cur.fetchall()
    dataCuentasCliente = data
    cur.close()
    return dataCuentasCliente

def TraerDataCuentasPorMoneda(id, moneda):    
    cur = mysql.connection.cursor()
    cur.execute("SELECT C.IDCUENTA, B.NOMBRE , C.NUMERO_CUENTA, C.NOMBRE_TITULAR, REPLACE (REPLACE(C.IDMONEDA, 1, 'SOLES'), 2, 'DOLARES') FROM m_cuenta C INNER JOIN de_banco B ON C.IDBANCO = B.IDBANCO  WHERE IDCLIENTE = '" + id + "' AND IDMONEDA = '" + moneda + "' ")
    data = cur.fetchall()
    dataCuentasCliente = data
    cur.close()
    return dataCuentasCliente

def ExisteUsuarioResetPass(id, token):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM m_cliente WHERE ID = '" + id + "' AND TOKEN = '" + token + "'")
    data = cur.fetchall()
    cur.close()
    if(len(data) == 1):
        return True
    else:
        return False

def ResetPasswordUser(id, token, newPassword):
    newPasswordHash = generate_password_hash(newPassword)
    newToken = str(uuid.uuid4())
    cur = mysql.connection.cursor()
    cur.execute("UPDATE m_cliente SET PASSWORD_HASH = '" + newPasswordHash +"' , TOKEN = '" + newToken + "' WHERE ID = '" + id + "' AND TOKEN = '" + token + "'")
    mysql.connection.commit()
    return redirect(url_for('Index'))


def write_fernet_key():
    """
    Generates a key and save it into a file
    """
    key = Fernet.generate_key()
    with open("key.key", "wb") as key_file:
        key_file.write(key)

def EsCorrectoPasswordHash(correo, password):
    cur = mysql.connection.cursor() 
    #cur.execute("SELECT * FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "' AND PASSWORD_HASH = '" + passwordHash + "'" )
    cur.execute("SELECT PASSWORD_HASH FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "' " )
    data = cur.fetchall()
    data2 = data[0]
    passwordHash = data2[0]
    cur.close()
    if check_password_hash(passwordHash, password):
        return True
    else:
        return False

def EsCorrectoPasswordHash2():
    if check_password_hash('pbkdf2:sha256:50000$8p5FhkoZ$6474e973bdd18688237dd5afcd277bfc3cc1bb1b6fe5e42a5a0c09e91f7b8728', 'lolopo'):
        print('Validacion correcta')
    else:
        print('Validacion incorrecta')
    return redirect(url_for('login')) 

@app.route('/restart-password-f/<id>/<token>')
def get_data_user(id,token):
    cur = mysql.connection.cursor()
    cur.execute("SELECT ID, CORREO_ELECTRONICO, TOKEN FROM m_cliente WHERE ID = %s AND TOKEN = %s", [id,token], )   ###The reasoning is that execute's second parameter represents a list of the objects to be converted
    data = cur.fetchall()
    return render_template('edit-contact.html', contact = data[0]) 


@app.route('/mail/<id>/<token>', methods=['GET','POST'])
def MailClass():
    #apikey = "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"
    
    url = "http://localhost:3000/reset-password/"

    """ 
    params = {
        "receiver_email_address": "royerleandroroblesvega@gmail.com",
    }
    correoweex.enviarCorreo(params) 
    """

    message = Mail(
        from_email='alonsog@we-ex.pe',
        to_emails='freddychpo@gmail.com',
        subject='Recuperacion de contraseña',
        html_content='Para crear su nueva contraseña por favor ingresa al siguiente link en el navegador: ')
    try:
        #sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        #sg = SendGridAPIClient(os.environ.get(apikey))
        sg = SendGridAPIClient('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')
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
        print("try")
    except Exception as e:
        print(e)
        print(e.body)
        print("exception")
    return "envio de mail"


def validateLoginRequired():
    url = request.url
    #print(url)
    session.permanent == True
    #print("dddsssssdd")

   # print(request.path)

    if 'user' in session and request.path == '/login':
        username = session['user']
        print("logueado y redireccionar")
        #return render_template('inicio.html', nameUser = 'name')
        return redirect(url_for('Cuenta'))
        """ if request.path == '/login':
            print('ggggggggggggg')
            return redirect(url_for('Inicio')) """
        print("logueado y redireccionar")

    else:
        print("no logueado")
        return redirect(url_for('login'))


""" @app.route('/home')
def Home():
    #validateLoginRequired()
    #print(str(uuid.uuid4()))
    if uriApp == 'app' :
        session['uriApp']= uriApp

    dataTipoCambio = TraerTipoCambioDolarSimulacion()
    session["dataTC"] = dataTipoCambio
    #print(dataTipoCambio)
    return render_template('home.html', dataTC = dataTipoCambio) """

def getSesiones():
    #validateLoginRequired()
    session.permanent == True
    sesions = {
        "nameUser": session['nameUser'],
        "role": session['role']
    }
    return sesions

def putSessions(function):
    def injectSession():
        #var_uppercase = function().upper()
        var_uppercase = 'fffff'
        print("resultado")
        return var_uppercase
    return injectSession

@app.route('/inicio')
#@login_required
#@putSessions
def Inicio():           
    #validateLoginRequired()
    session.permanent == True

    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)

    idCliente = obtenerIdClienteUsuLogueado(session['user'])
    session['idCli']=idCliente
    name = obtenerNombreUserLogueado(session['user'])
    session['nameUser'] = name
    session['tipoDoc'] = obtenerTipoDocUsuLogueado(session['user'])
    session['numDoc'] = obtenerNumDocUsuLogueado(session['user'])
    print("inicio form")
    role = session['role']
    print(getSesiones())
    sesions = getSesiones()
    return render_template('inicio.html', nameUser = name, role = role, sesions=sesions)

@app.route('/logout')
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for('login'))

def addSesion():
    session.permanent == True
    print("add ssss")
    #session['role'] = 3

@app.before_request
def before_request_func():
    session.permanent == True
    #session['role'] = session['role']
    #session['nameUser'] = session['nameUser']
    #print(session)
    print("before_request is running!")
    #return "Intercepted by before_request"

@app.route('/cuenta')
#@login_required
def Cuenta():
    session.permanent == True
    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)

    key = open("key.key", "rb").read()
    f = Fernet(key)
    idCLiente= session['idCli']
    
    dataCuentasUsuario = TraerDataCuentas(str(idCLiente))
    listCuentasUsuario = list(dataCuentasUsuario)
    numeroRegistros = len(listCuentasUsuario)

    items = []
    for i in range(0, numeroRegistros):
        #i = str(i)
        tupleAux = tuple(listCuentasUsuario[i])
        # dict == {}
        # you just don't have to quote the keys
        #an_item = dict(banco=tupleAux[0], cuenta=tupleAux[1], titular=tupleAux[2], moneda=tupleAux[3])
        an_item = dict(id = tupleAux[0], banco= tupleAux[1], cuenta= f.decrypt(tupleAux[2]).decode('utf-8') , titular=f.decrypt(tupleAux[3]).decode('utf-8'), moneda=tupleAux[4])
        items.append(an_item)
   
    session["items"] = items
    role = session['role']
    #session['role'] = 1
    #print(items)
    sesions = getSesiones()
    #addSesion()
    return render_template('cuenta.html', role = role, sesions=sesions)

@app.route('/eliminarCuenta/<string:id>')
def delete_account(id):
    cur = mysql.connection.cursor() 
    cur.execute("DELETE FROM m_cuenta WHERE IDCUENTA = {0} " .format(id))
    mysql.connection.commit()
    flash('Cuenta Eliminada Correctamente')
    return redirect(url_for('Cuenta'))

@app.route('/editarCuenta/<id>')
def edit_account(id):
    cur = mysql.connection.cursor() 
    cur.execute('SELECT * FROM m_cuenta WHERE IDCUENTA = %s',[id] )
    data = cur.fetchall()
    
    cur2 = mysql.connection.cursor() 
    cur2.execute('SELECT * FROM de_moneda')
    data2 = cur2.fetchall()

    cur3 = mysql.connection.cursor() 
    cur3.execute('SELECT * FROM de_banco')
    data3 = cur3.fetchall()

    key = open("key.key", "rb").read()
    f = Fernet(key)
    tupleAux = tuple(data[0])
    an_item = dict(id = tupleAux[0], banco= tupleAux[2], cuenta= f.decrypt(tupleAux[5]).decode('utf-8') , titular=f.decrypt(tupleAux[6]).decode('utf-8'), moneda=tupleAux[4])
    print("Cuenta a editar")
    print(an_item)

    return render_template('edit-cuenta.html', account = an_item, tipoMonedas = data2 , listBanco = data3 )

@app.route('/updateAccount/<id>', methods = ['POST'])
def update_account(id):
    if request.method == 'POST':
        
        key = open("key.key", "rb").read()
        f = Fernet(key)

        banco = request.form.get('Banco', None)        
        tipoMon = request.form.get('TipoMoneda', None)

        numCuenta = request.form['NumeroCuenta']
        numCuentaEncrypt = f.encrypt(numCuenta.encode('utf-8'))
        nomTitu = request.form['NombreTitular']
        nomTituEncrypt = f.encrypt(nomTitu.encode('utf-8'))

        cur = mysql.connection.cursor() 
        cur.execute(""" 
            UPDATE m_cuenta 
            SET IDBANCO = %s, IDMONEDA= %s, NUMERO_CUENTA= %s, NOMBRE_TITULAR = %s 
            WHERE IDCUENTA = %s 
            """ ,(banco , tipoMon, numCuentaEncrypt, nomTituEncrypt, id))
        flash('Cuenta Actualizada Correctamente')
        mysql.connection.commit()
        return redirect(url_for('Cuenta'))

@app.route('/datos-personales')
#@login_required
def DatosPersonales():

    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)   
            
    user = session['user']
    cur = mysql.connection.cursor() 
    cur.execute("SELECT * FROM m_cliente WHERE CORREO_ELECTRONICO = '" + user + "'")
    data = cur.fetchall()
    cur.close()


    return render_template('datos-personales.html', contact = data[0])

@app.route('/updatePersonalInfo', methods = ['POST'])
def updatePersonalInfo():
    if request.method == 'POST':
        telefono = request.form['Telefono']
        ocupacion = request.form['Ocupacion']

        try:
            cur = mysql.connection.cursor()             
            cur.execute("UPDATE m_cliente SET CELULAR = %s, OCUPACION = %s WHERE ID = %s", 
                (telefono,ocupacion, session['idCli'] ))
            flash('Datos Actualizados')

            mysql.connection.commit()
        except:
            print ("ERROR !")
            flash('Error al actualizar datos personales')
            return redirect(url_for('DatosPersonales'))

        return redirect(url_for('DatosPersonales'))

def listarOrdenesByIdCliente(idCliente, rolId):
    id= str(idCliente)
    cur = mysql.connection.cursor()
    if rolId == '1':
        cur.execute("SELECT O.ID,O.CODINTERNO, O.CODORDEN,O.MTOENVIO, REPLACE (REPLACE(O.MONEDAENVIO, 1, 'SOLES'), 2, 'DOLARES'), O.MTORECIBO, REPLACE (REPLACE(O.MONEDARECIBO, 1, 'SOLES'), 2, 'DOLARES'), REPLACE(REPLACE (REPLACE(O.ESTADO, 1, 'PENDIENTE'), 2, 'REALIZADO'), 3, 'ANULADO'),B.NOMBRE, C.NUMERO_CUENTA, C.NUMDOC, O.RUTA_COMPROBANTE FROM m_orden O INNER JOIN m_cuenta C ON O.IDCUENTARECIBO = C.IDCUENTA INNER JOIN de_banco B ON C.IDBANCO = B.IDBANCO  WHERE C.IDCLIENTE = "+ id + " ORDER BY FECHAHORACREACION DESC ")		
    elif rolId == '2':
        cur.execute("""
        SELECT O.ID, O.CODINTERNO, O.CODORDEN,O.MTOENVIO, REPLACE (REPLACE(O.MONEDAENVIO, 1, 'SOLES'), 2, 'DOLARES'),
            O.MTORECIBO, REPLACE (REPLACE(O.MONEDARECIBO, 1, 'SOLES'), 2, 'DOLARES'),
            REPLACE(REPLACE (REPLACE(O.ESTADO, 1, 'PENDIENTE'), 2, 'REALIZADO'), 3, 'ANULADO'),
            B.NOMBRE,C.NUMERO_CUENTA, C.NUMDOC,  O.RUTA_COMPROBANTE
            FROM m_orden O INNER JOIN m_cuenta C
            ON O.IDCUENTARECIBO = C.IDCUENTA 
            INNER JOIN de_banco B
            ON C.IDBANCO = B.IDBANCO 
            ORDER BY FECHAHORACREACION DESC
                   """)
    data = cur.fetchall()
    cur.close()
    return data

def obtenerNombreUserLogueado(correo):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT NOMBRE FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "'")
    data = cur.fetchall()
    nombreUsuarioLogueado = data[0][0]

    print(nombreUsuarioLogueado)
    cur.close()
    return nombreUsuarioLogueado

def obtenerIdClienteUsuLogueado(correo):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT ID FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "'")
    data = cur.fetchmany(1)
    idCliente = data[0][0]
    print("Obteniendo Id de cliente logueado")
    print (idCliente)
    cur.close()
    return idCliente

def obtenerTipoDocUsuLogueado(correo):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT ID_TIPO_DOCUMENTO FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "'")
    data = cur.fetchmany(1)
    tipoDoc = data[0][0]
    print("Obteniendo tipo doc de cliente logueado")
    print (tipoDoc)
    cur.close()
    return tipoDoc

def obtenerNumDocUsuLogueado(correo):
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT NUMERO_DOCUMENTO FROM m_cliente WHERE CORREO_ELECTRONICO = '" + correo + "'")
    data = cur.fetchmany(1)
    numDoc = data[0][0]
    print("Obteniendo Num doc clieente logueado")
    print (numDoc)
    cur.close()
    return numDoc


@app.route('/ordenes')
#@login_required
def Ordenes():
    session.permanent == True
    print("Listar orden")
    print(session['role'])
    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)

    key = open("key.key", "rb").read()
    f = Fernet(key)

    listOrdenes = listarOrdenesByIdCliente(session['idCli'], session['role'])
    numeroRegistros = len(listOrdenes)

    itemsOrder = []
    for i in range(0, numeroRegistros):
        #i = str(i)
        tupleAux = tuple(listOrdenes[i])
        # dict == {}
        # you just don't have to quote the keys
        #an_item = dict(banco=tupleAux[0], cuenta=tupleAux[1], titular=tupleAux[2], moneda=tupleAux[3])
        an_item = dict(id = tupleAux[0],codInt = tupleAux[1], codOrden= tupleAux[2], mtoEnvio= tupleAux[3], monEnvio= tupleAux[4],
        mtoRecibo= tupleAux[5], monRecibo= tupleAux[6], estado= tupleAux[7], banco = tupleAux[8], cuenta= f.decrypt(tupleAux[9]).decode('utf-8') ,
        numDoc=f.decrypt(tupleAux[10]).decode('utf-8'), rutaComprobante= tupleAux[11] )
        itemsOrder.append(an_item)

    session["itemsOrder"] = itemsOrder
    sesions = getSesiones()
    #addSesion()

    return render_template('ordenes.html', nameUser = session['nameUser'], sesions=sesions)

@app.route('/editarOrden/<id>')
def edit_orden(id):
    cur = mysql.connection.cursor() 
    cur.execute('SELECT * FROM m_orden WHERE ID = %s',[id] )
    data = cur.fetchall()
    print (data[0])
    return render_template('edit-orden.html', order = data[0])

@app.route('/updateOrder/<id>', methods = ['POST'])
def update_order(id):
    if request.method == 'POST':
        
        estado = request.form['estado']

        cur = mysql.connection.cursor() 
        cur.execute(""" 
            UPDATE m_orden
            SET ESTADO= %s
            WHERE ID = %s 
            """ ,(estado, id))
        flash('Orden Actualizada Correctamente')
        mysql.connection.commit()
        return redirect(url_for('Ordenes'))

@app.route('/editarNumOperacion/<id>')
def edit_numOperacion(id):
    cur = mysql.connection.cursor() 
    cur.execute('SELECT * FROM m_orden WHERE ID = %s',[id] )
    data = cur.fetchall()
    print (data[0])
    return render_template('edit-numOperacion.html',  order = data[0])

@app.route('/updateNumOperation/<id>', methods = ['POST'])
def update_numOperation(id):
    if request.method == 'POST':
        NumeroOperacion = request.form['NumeroOperacion']
        f = request.files['ComprobanteOperacion']
        nombre =f.filename.strip()
        print('Subiendo imagen')
        print(nombre)
        print(id)
        print(NumeroOperacion)
        if f.filename != '':
            filename = secure_filename(f.filename.strip())
            f.save(os.path.join(app.config["UPLOAD_FOLDER"] ,filename))

        cur = mysql.connection.cursor()
        cur.execute("UPDATE m_orden SET CODORDEN = %s, RUTA_COMPROBANTE = %s WHERE ID = %s", 
                ( NumeroOperacion, nombre, id)) 
        mysql.connection.commit()
        
        #Invocar API Sendblue
        sendMailOperationConfirm(session["user"], session['nameUser'], 2)

        return redirect(url_for('Ordenes'))

@app.route("/uploads/<filename>")
def get_file(filename):

    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

""" @app.route('/')
def Redirect():
    dataTipoCambio = TraerTipoCambioDolarSimulacion()
    
    print(app.config["SERVER_NAME"])
    return render_template('home.html', dataTC = dataTipoCambio) """

@app.route('/register')
def Index(): ## funcion para manejar la peticion
    cur = mysql.connection.cursor() 
    cur.execute('SELECT * FROM de_tipo_documento')
    data = cur.fetchall()
    cur2 = mysql.connection.cursor()
    cur2.execute('SELECT * FROM de_tipo_persona')
    data2 = cur2.fetchall()
    #filas  = cur2.rowcount
    cur.close()
    cur2.close()
    return render_template('add-client.html', tipo_documentos = data, tipo_persona = data2) #flask ya tiene configurado el nombre de la carpeta templates


@app.route('/add_test_2', methods=['GET','POST'])
def add_test_2():
    cur = mysql.connection.cursor() 
    cur.execute('SELECT NOMBRE_TITULAR, NUMERO_CUENTA, NUMDOC FROM m_cuenta_prueba')
    data = cur.fetchall()

    key = open("key.key", "rb").read()
    f = Fernet(key)

    for x in data:
        for y in x:
            decrypted_encrypted = f.decrypt(y)
            decrypted_encrypted_decoded = decrypted_encrypted.decode('utf-8') 
            print(decrypted_encrypted_decoded)

    return redirect(url_for('Index'))



@app.route('/test_01', methods=['GET', 'POST'])
def test_01():
    
    #key=frt.generate_key()
    key = open("key.key", "rb").read()

    cur = mysql.connection.cursor() 
    cur.execute('SELECT NOMBRE_TITULAR, NUMERO_CUENTA, NUMDOC FROM m_cuenta_prueba')
    data = cur.fetchall()


    for x in data:
        #s = "message"
        #s = data[x]
        """ s = x
        print('input string: {0}'.format(s))
        #key=base64.b64encode(key) #no need to do this
        print('key: {0}, type: {1}'.format(key, type(key)))
        f=frt(key)
        token = f.encrypt(s.encode('utf-8')) #need to convert the string to bytes
        print ('encrypted: {0}'.format(token))
        output = f.decrypt(token)
        output_decoded = output.decode('utf-8')
        print ('decrypted: {0}'.format(output_decoded)) """
        print(x)

    for x in data:
        for y in x:
            print(y)   
            """ s = y
            print('input string: {0}'.format(s))
            #key=base64.b64encode(key) #no need to do this
            print('key: {0}, type: {1}'.format(key, type(key)))
            f=frt(key)
            token = f.encrypt(s.encode('utf-8')) #need to convert the string to bytes
            print ('encrypted: {0}'.format(token)) """
            f=frt(key)
            token = y
            output = f.decrypt(token)
            output_decoded = output.decode('utf-8')
            print ('decrypted: {0}'.format(output_decoded))


    thistuple = ("apple", "banana", "cherry")
    for x in thistuple:
        print(x)        

    return redirect(url_for('Index'))

@app.route('/add_test', methods=['GET','POST'])
def add_test():
    if request.method == 'GET':
        return render_template('pruebaEncriptar.html')
    if request.method == 'POST':
        NumeroCuenta = request.form['NumeroCuenta']
        NombreTitular = request.form['NombreTitular']
        NumeroDocumento = request.form['NumeroDocumento']
        

        key = open("key.key", "rb").read()
        """ key = load_key() """

        print(NumeroCuenta)
        print(NombreTitular)
        print(NumeroDocumento)

        """    
        NumeroCuentaEncoded = NumeroCuenta.encode('utf-8')
        NombreTitularEncoded = NombreTitular.encode('utf-8')
        NumeroDocumentoEncoded = NumeroDocumento.encode('utf-8')
        """
        f = Fernet(key)

        """  
        NumeroCuentaEncrypted = f.encrypt(NumeroCuentaEncoded)
        NombreTitularEncrypted = f.encrypt(NombreTitularEncoded)
        NumeroDocumentoEncrypted = f.encrypt(NumeroDocumentoEncoded) 
        """

        NumeroCuentaEncrypted = f.encrypt(NumeroCuenta.encode('utf-8'))
        NombreTitularEncrypted = f.encrypt(NombreTitular.encode('utf-8'))
        NumeroDocumentoEncrypted = f.encrypt(NumeroDocumento.encode('utf-8'))

        print(NumeroCuentaEncrypted)
        print(NombreTitularEncrypted)
        print(NumeroDocumentoEncrypted)

        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO m_cuenta_prueba
            VALUES('', %s, %s, %s)
            """, 
        (NombreTitularEncrypted, NumeroCuentaEncrypted, NumeroDocumentoEncrypted))
        mysql.connection.commit()    
        return redirect(url_for('Index'))




@app.route('/add_client', methods=['GET','POST'])
def add_client():
    print('print inicio add cliente')
    if request.method == 'POST':
        
        nombre = request.form['Nombre']
        apellidoPaterno = request.form['ApellidoPaterno']
        apellidoMaterno = request.form['ApellidoMaterno']
        correoElectronico = request.form['CorreoElectronico']
        celular = request.form['Celular']
        password = request.form['password   ']
        token = str(uuid.uuid4())
        tipoDocumento = request.form.get('TipoDocumento', None)
        numeroDocumento = request.form['NumeroDocumento']
        fechaEmisionDocumento = request.form['FechaEmisionDocumento']
        personaPolitica = request.form.get('PersonaPolitica', None)
        tipoPersona = request.form.get('TipoPersona', None)
        ocupacion = request.form['Ocupacion']
        fotoCliente = '' #app.config["IMAGE_UPLOADS"] + "\\" + filenameFoto
        f1 = request.files['imagenFotoDocFrontal']
        nombreF =f1.filename.strip()
        if nombreF != '':
            filename = secure_filename(nombreF)
            f1.save(os.path.join(app.config["UPLOAD_DNI"] ,filename))
        fotoDocumento = nombreF

        f2 = request.files['imagenFotoDocPosterior']
        nombreP =f2.filename.strip()
        if nombreP != '':
            filename = secure_filename(nombreP)
            f2.save(os.path.join(app.config["UPLOAD_DNI"] ,filename))
        fotoDocumentoB = nombreP
        
        now = datetime.datetime.now()
        
        cur = mysql.connection.cursor()
        
        try :
            cur.execute("""
                INSERT INTO m_cliente
                VALUES(null, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, 
            (nombre, apellidoPaterno, apellidoMaterno, correoElectronico,celular, generate_password_hash(password), 
            token, tipoDocumento, numeroDocumento, fechaEmisionDocumento, personaPolitica, tipoPersona, ocupacion,
            fotoCliente, fotoDocumento, fotoDocumentoB, now, '1'))#uso de tupla
            mysql.connection.commit()    

            
            #Invocar API sendblue
            sendMailOperationConfirm(correoElectronico, nombre, 1)


            flash('Usuario registrado correctamente')
            return redirect(url_for('login'))
        except:
            print ("ERROR !")
            flash('Numero de documento o email del usuario ya existe en el sistema')
            return redirect(url_for('Index'))
            
        #return redirect(url_for('login'))
        #return 'received'
""" 
@app.route('/edit/<id>')
def get_contact(id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM CONTACTS WHERE ID = %s", [id])   ###The reasoning is that execute's second parameter represents a list of the objects to be converted
    data = cur.fetchall()
    return render_template('edit-contact.html', contact = data[0])   
 """

"""  @app.route("/user")
 def user():
    if "user" in session:
         user = session["user"]
         return f"<h1>{user}</h1>"
    else: """

@app.route("/tasaCambioAdmin" , methods=['GET','POST'])
#@login_required
def tasaCambioAdmin():
    
    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)
        
    dataTipoCambio = TraerTipoCambioDolarSimulacion()
   
    if request.method == 'POST':
        tasaCompra = request.form['tasaCompra']
        tasaVenta = request.form['tasaVenta']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE tasa_cambio
                SET COMPRA = %s,
                    VENTA = %s
                WHERE id = %s
        """, (tasaCompra, tasaVenta, 1))
        mysql.connection.commit()
        flash('Tasa actuazalida Correctamente')

        return redirect(url_for('tasaCambioAdmin')) 
    else:
        print("GET")
        return render_template("tasa-cambio-admin.html", dataTC = dataTipoCambio,  )

@app.route("/tasa-cambio-post" , methods=['GET','POST'])
def tasaCambioPost():
    if request.method == 'POST':
        dataTipoCambio = TraerTipoCambioDolarSimulacion()
        session["dataTC"] = dataTipoCambio

        tasaCompra = request.form['tasaCompra']
        session["tasaCompra"] = tasaCompra    

        tasaVenta = request.form['tasaVenta']
        session["tasaVenta"] = tasaVenta

        return redirect(url_for('tasaCambioAdmin')) 

@app.route("/operacion-cambio-post" , methods=['GET','POST'])
def operacionCambioPost():
    if request.method == 'POST':
        dataTipoCambio = TraerTipoCambioDolarSimulacion()
        session["dataTC"] = dataTipoCambio

        montoEnviar = request.form['montoEnviar']
        session["montoEnviar"] = montoEnviar    

        montoRecibir = request.form['montoRecibir']
        session["montoRecibir"] = montoRecibir

        monedaCambio = request.form['monedaCambio']
        session["monedaCambio"] = monedaCambio

        monedaCambioOpe = monedaCambio[8:9]
        session["monedaCambioOpe"] = monedaCambioOpe

        tipoCambio = session["dataTC"]

        if (monedaCambio == "Moneda: Dólares a Soles"):
            session["tipoCambio"] = tipoCambio[0];

        if (monedaCambio == "Moneda: Soles a Dólares"):
            session["tipoCambio"] = tipoCambio[1];

        return redirect(url_for('operacionCambioCuentas')) 



@app.route("/operacion-cambio" , methods=['GET','POST'])
def operacionCambio():
    dataTipoCambio = TraerTipoCambioDolarSimulacion()
    
    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)

    if request.method == 'POST':   
        """ dataTipoCambio = TraerTipoCambioDolarSimulacion()
        session["dataTC"] = dataTipoCambio    """

        print("POST")
        """ return redirect(url_for('operacionCambioCuentas', dataTC = dataTipoCambio  )) """
        return redirect(url_for('operacionCambioCuentas')) 
    else:
        print("GET")
        return render_template("operacion-cambio.html", dataTC = dataTipoCambio,  )

def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData

@app.route("/actualizar/numero/operacion", methods=['GET','POST'])
def operacionActualizarNumeroOperacion():
    if request.method == 'POST':
        print("POST")
        if "GuardarOperacion" in request.form:
            codIn= session["codinterno"]
            print("Actualizar con tipo operacion")
            NumeroOperacion = request.form['NumeroOperacion']
            
            f = request.files['ComprobanteOperacion']
            nombre = f.filename
            if f.filename != '':
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"] ,filename))

            cur = mysql.connection.cursor()
            try :
                cur.execute("""
                    UPDATE m_orden
                    SET CODORDEN = %s ,
                        RUTA_COMPROBANTE = %s
                    WHERE CODINTERNO = %s
                    """, 
                    ( NumeroOperacion, nombre.strip(), codIn)) 
                mysql.connection.commit()

                #Invocar API sendblue
                sendMailOperationConfirm(session["user"], session['nameUser'], 2)
                
                return redirect(url_for('Ordenes'))
            except:
                print ("ERROR !")
                flash('Error al guardar comprobante')
                return redirect(url_for('operacionCambioCuentas'))
    else:
        return redirect(url_for('operacionCambioCuentas'))

@app.route("/operacion/validar/<codinterno>", methods=['GET','POST'])
#@login_required
def operacionValidarOrden(codinterno):
    
    return render_template("orden.html")

@app.route("/procesar-orden", methods=['GET','POST'])
#@login_required
def operacionProcesarOrden():
    if request.method == 'POST' and request.form['procesar_orden'] == 'Procesar':
        montoEnviar = session["montoEnviar"]
        montoRecibir = session["montoRecibir"]
        monedaCambio = session["monedaCambio"]
        tipoCambio = session["dataTC"]
    
        f = request.form
        for key in f.keys():
            for value in f.getlist(key):
                print(key, " : ", value)

        cad=""

        for item,value in request.form.items():
            cad+="{}:{}<br/>".format(item,value)

        return cad

        #return montoEnviar + ' ' + montoRecibir + ' ' +  monedaCambio + ' ' + str(tipoCambio) + ' ' + str(request.form)
    else:
        return "no entro al post"





@app.route("/operacion-cambio/cuentas", methods=['GET','POST'])
#@login_required
def operacionCambioCuentas():
    session.permanent == True
    
    if "role" not in session:
        abort(404)

    if "user" not in session:
        abort(404)

    if "idCli" not in session:
        abort(404)

    idCliente = session['idCli']
    monedaOperacionFin = '0'
    if request.method == 'POST':
        if "GuardarCuenta" in request.form:
            key = open("key.key", "rb").read()
            f = Fernet(key)
            
            Banco = request.form['Banco']
            NumeroCuenta = request.form['NumeroCuenta']            
            TipoMoneda = request.form['TipoMoneda']

            NombreTitular = request.form['NombreTitular']
            tipoDocumento = request.form.get('TipoDocumento', None)
            NumeroDocumento = request.form['NumeroDocumento']

            if NombreTitular == '' :
                NombreTitular = session['nameUser']
                tipoDocumento = session['tipoDoc']
                NumeroDocumento = session['numDoc']   
            
            NumeroCuentaEncrypted = f.encrypt(NumeroCuenta.encode('utf-8'))
            NombreTitularEncrypted = f.encrypt(NombreTitular.encode('utf-8'))
            NumeroDocumentoEncrypted = f.encrypt(NumeroDocumento.encode('utf-8'))

            try:
                cur = mysql.connection.cursor()
                cur.execute("""
                    INSERT INTO m_cuenta
                    VALUES(0, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, 
                ( idCliente, Banco, '0', TipoMoneda, NumeroCuentaEncrypted, NombreTitularEncrypted, tipoDocumento, NumeroDocumentoEncrypted )) 
                mysql.connection.commit()     
            except:
                print ("ERROR !")
                
            return redirect(url_for('operacionCambioCuentas'))
            
        if "ProcesarOrden" in request.form:
            print("Procesar Orden")
            codinterno = random.randint(10000, 99999)
            session["codinterno"] = codinterno

            montoEnviar = session["montoEnviar"]
            montoRecibir = session["montoRecibir"]
            monedaCambio = session["monedaCambio"]
            tipoCambio = session["dataTC"]
            print("Tipo de Cambio = " , monedaCambio)
            if(monedaCambio == "Moneda: Dólares a Soles"):
                    monedaEnvio = ObtenerIdMoneda('USD')[0][0]
                    monedaRecibo = ObtenerIdMoneda('PEN')[0][0]
                    mtoTipoCambio = tipoCambio[0]
                    session["strMonedaEnvio"] = 'Dólares' 
                    session["strMonedaRecibo"] = 'Soles'
                    session["NroCuentaEmpresa"] = '2003003608422'
            elif(monedaCambio == "Moneda: Soles a Dólares"):
                    monedaEnvio = ObtenerIdMoneda('PEN')[0][0]
                    monedaRecibo = ObtenerIdMoneda('USD')[0][0]
                    mtoTipoCambio = tipoCambio[1]
                    session["strMonedaEnvio"] = 'Soles' 
                    session["strMonedaRecibo"] = 'Dólares'
                    session["NroCuentaEmpresa"] = '2003003608245'

            BancoEnvio = request.form.get('BancoEnvio', None)
            CuentaRecibo = request.form.get('CuentaRecibo', None)

            stringLength = 7
            lettersAndDigits  = string.ascii_uppercase + string.digits
            """ nro_orden = ''.join(random.sample(lettersAndDigits, stringLength))

            while ExisteOrden(nro_orden) == True:
                stringLength = 7
                lettersAndDigits  = string.ascii_uppercase + string.digits
                nro_orden = ''.join(random.sample(lettersAndDigits, stringLength))

                if ExisteOrden(nro_orden) == False:
                    break

            session["nro_orden"] = nro_orden """

            #now = datetime.datetime.now() -  datetime.timedelta(hours=1)
            now = datetime.datetime.now()
            nowEnd = now + datetime.timedelta(minutes=20)
            session["strHoraInicio"] = str(now.strftime("%d/%m/%Y %H:%M:%S"))
            session["strHoraFin"] = str(nowEnd.strftime("%d/%m/%Y %H:%M:%S"))
            #now = datetime.now()
            #session["strHoraraInicio"] = str(now)
            print("antes de insertar orden")
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO m_orden
                VALUES(0, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, 
            ( codinterno, '', idCliente, now, montoEnviar, monedaEnvio, BancoEnvio, montoRecibir, monedaRecibo, CuentaRecibo, mtoTipoCambio, '1', '')) 
            mysql.connection.commit()   

            return redirect(url_for('operacionValidarOrden', codinterno = codinterno))
            
    elif request.method == 'GET':

        key = open("key.key", "rb").read()
        f = Fernet(key)

        dataBancoDeDondeEnvias = TraerDataBancoDeDondeEnvias()
        session["dataBanco1"] = dataBancoDeDondeEnvias  

        dataBanco = TraerDataBanco()
        session["dataBanco2"] = dataBanco  


        dataTipDoc = TraerDataTipDoc()
        session["dataTipDoc"] = dataTipDoc 

        monedaOperacion = session["monedaCambioOpe"]
        
        ## Si la moneda de operacion final es de 'Dolares' a 'Soles' --> Se debe mostrar las cuentas en soles
        monedaOpFinal = '1' if monedaOperacion == 'D' else '2'

        monedaBanco = 'Dolares' if monedaOperacion == 'D' else 'Soles'
        session["monedaBancoTemp"] = monedaBanco
        monedaCuenta = 'Soles' if monedaOperacion == 'D' else 'Dolares'
        session["monedaCuentaTemp"] = monedaCuenta

       

        dataCuentasUsuario = TraerDataCuentasPorMoneda(str(idCliente), monedaOpFinal)
        session["dataCuentasUsuario"] = dataCuentasUsuario

        #dataCuentasUsuario = TraerDataCuentas(str(idCliente))
        listCuentasUsuario = list(dataCuentasUsuario)

        numeroRegistros = len(listCuentasUsuario)

        items = []
        for i in range(0, numeroRegistros):
            #i = str(i)
            tupleAux = tuple(listCuentasUsuario[i])
            # dict == {}
            # you just don't have to quote the keys
            #an_item = dict(banco=tupleAux[0], cuenta=tupleAux[1], titular=tupleAux[2], moneda=tupleAux[3])
            an_item = dict( id = tupleAux[0] ,banco= tupleAux[1], cuenta= f.decrypt(tupleAux[2]).decode('utf-8') , titular=f.decrypt(tupleAux[3]).decode('utf-8'), moneda=tupleAux[4])
            items.append(an_item)
    
        
        session["items"] = items

        return render_template("cuentas.html")

oauth = OAuth(app)
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register( 
    name = "google",
    client_id = weexConstants.CLIENT_ID,
    client_secret= weexConstants.SECRET_ID,
    server_metadata_url = CONF_URL,
    client_kwargs ={
        'scope' : 'openid email profile'
    }
    )

# @app.route('/login2')
# def login2():
#     redirect_url = url_for("auth", _external=True)
#     return oauth.google.authorize_redirect(redirect_url)

@app.route('/login3', methods=['GET','POST'])
def login3():    
    uriApp=request.path[1:4]
    if uriApp == 'app' :
        session['uriApp']= uriApp

    if 'user' in session and request.path == '/login3':
        print('redirect')
        return redirect(url_for('Cuenta'))
    return render_template("login2.html")

@app.route('/auth')
def auth():
    token = oauth.google.authorize_access_token()
    response = oauth.google.parse_id_token(token)
    print(response)
    return redirect("/")

@app.route('/')
@app.route('/login', methods=['GET','POST'])
def login():
    
    session['uriBase']= request.url_root
    uriApp=request.path[1:4]
    if uriApp == 'app' :
        session['uriApp']= uriApp
        session['uriBase']= request.url_root + uriApp 
        
    print("Validando uri")
    print(session['uriBase'])

    if 'user' in session and request.path == '/login':
        print('redirect')
        return redirect(url_for('Cuenta'))
    return render_template("login.html")


@app.route('/recover_account', methods=['GET','POST'])
def recoverAccount():
    #url = "http://weex.pe/reset_password/"
    #url = "http://127.0.0.1:5000/reset_password/"
    session['uriBase']= request.url_root
    uriApp=request.path[1:4]
    if uriApp == 'app' :
        session['uriApp']= uriApp
        session['uriBase']= request.url_root + uriApp 
        
    print("Validando uri")
    print(session['uriBase'])
    
    if request.method == 'POST':
        correo = request.form['correo']
        cur = mysql.connection.cursor()
        cur.execute("SELECT ID, CORREO_ELECTRONICO,TOKEN,NOMBRE FROM m_cliente WHERE CORREO_ELECTRONICO = %s", [correo])   ###The reasoning is that execute's second parameter represents a list of the objects to be converted
        data = cur.fetchall()
        data2 = data[0]
        id = data2[0]
        token = data2[2]
        clientName = data2[3]

        sendMailResetPassword(correo, clientName,id,token,session["uriBase"])
        

        return redirect(url_for('login'))

        #return render_template("reset-password.html")

    
@app.route('/reset-password', methods=['GET','POST'])
def resetPassword():    
    return render_template("reset-password.html")

@app.route('/reset_password/<id>/<token>', methods=['GET','POST'])
def reset_password(id, token):
    if request.method == 'POST':
        print('post_reset_password')
        password = request.form['password']
        passwordConfirm = request.form['passwordConfirm']
        
        if(password == passwordConfirm):
            if(ExisteUsuarioResetPass(id, token)):
                #actualizar a una nueva contrasena en base a paramtros: id y token
                ResetPasswordUser(id, token, passwordConfirm)
                print('se actualizo correctamente la contrasena del usuario')
                return redirect(url_for('Redirect'))
        else:
            print('los valores de la nueva contrasena y la confirmacion de la nueva contrasena no coinciden')
    else:
        print('get_reset_password', id, token)
        return render_template("reset-password.html", id = id, token = token)

@app.route('/loginValidate', methods=['GET','POST'])
def loginValidate():
    if request.method == 'POST':
        session.permanent == True
        user = request.form['username']
        password = request.form['password']

        passwordHashConvert = generate_password_hash(password)

        if(ExisteCliente(user)):
            #if(EsCorrectoPasswordHash(user, password)):
                #print('Inicio sesion correcto')

            rolUser = ObtenerRolByUser(user)
            print(rolUser)
            if(EsCorrectoPasswordHash(user, password)):
                flash('Inicio sesion correcto')
                #EsCorrectoPasswordHash(user,password)   
                #return render_template("index.html")
                session['user'] = user
                session['role'] = rolUser  
                
                return redirect(url_for('Inicio'))
               
            else:
                
                flash('Password incorrecto')
                return render_template("login.html")
        else:
            flash('no existe usuario')
            return render_template("login.html")

    

@app.route('/recover-account', methods=['GET'])
def recover_account():
    return render_template("recover-account.html")
        
@app.route('/update/<id>', methods = ['POST']) #methods es igual a un arreglo POST
def update_contact(id):
    if request.method == 'POST':
        fullname = request.form['fullname']
        phone = request.form['phone']
        email = request.form['email']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE CONTACTS
                SET fullname = %s,
                    email = %s,
                    phone =%s
                WHERE id = %s
        """, (fullname, email, phone, id))
        mysql.connection.commit()
        flash('Contact updated successfully')
        return redirect(url_for('Index'))


@app.route('/delete/<string:id>')
def delete_contact(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM CONTACTS WHERE ID = {0}'.format(id))
    mysql.connection.commit()
    flash('Contact Removed Successfully')
    return redirect(url_for('Index'))

def reverse_decorator(function):
    print('Inside reverse_decorator function')
    def reverse_wrapper():
        print('Inside reverse_wrapper function')

        """ if "user" in session:
            user = session["user"]
            return f"<h1>{user}</h1>" """

        session.permanent == True
        print("Listar orden")
        print(session['user'])	

        return 'Return reverse_wrapper function'
    return reverse_wrapper

@app.route('/test/acceso')
@reverse_decorator
def accesoTest():
    
    return "fff"


@app.route('/admin', methods=['GET','POST'])
def admin():
    print("admin")
    #validateLoginRequired()
    #if 'user' in session and request.path == '/login':
    #    print('redirect')
    #return redirect(url_for('Cuenta'))
    return render_template("admin.html")

# @login_manager.user_loader
# def load_user(username):
#     return User.query.filter_by(username = username).first()


# @login_manager.unauthorized_handler
# def unauthorized():
#     return redirect(url_for("login"))

# @login_manager.unauthorized_handler
# def unauthorized():
#     return redirect(url_for('Redirect'))


# class User(db.Document):
#     name = db.StringField()
#     password = db.StringField()
#     email = db.StringField()
#     def to_json(self):
#         return {"name": self.name,
#                 "email": self.email}
#     def is_authenticated(self):
#         return True
#     def is_active(self):
#         return True
#     def is_anonymous(self):
#         return False
#     def get_id(self):
#         return str(self.id)


# class User(UserMixin):
#   def __init__(self,id):
#     self.id = id

@login_manager.user_loader
def user_loader():
    # session.permanent == True
    # #session['user'] = user
    # if 'user' in session:
    #   username = session['user']
    # else:
    #     session['user'] = True 

    # print(session['user'])

    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve

    """
    return User.query.get(user_id)

if __name__ == '__main__':
   app.run(debug=True)
