from flask import Flask, render_template, request
from flask_socketio import SocketIO, send, emit
import threading
import random
from queue import Queue # Python 3.x

que = Queue()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)

clients = []
positionsClients = {}
countPlayers = 1

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('saludo')
def handleMessage(msg):
    print('Message: ' + msg)
    emit('saludo', msg, broadcast = True)

# Events to manage connections and disconnection events
@socketio.on('connect')
def test_connect():
    global countPlayers
    positions = createPositions()
    objectClient = { "id": request.sid, "intentos": 15, 'number': countPlayers, "correctos": 0, "incorrectos": 0 }
    clients.append(objectClient)
    positionsClients[request.sid] = positions # Agregar posiciones al objeto global
    print(positions)
    countPlayers = countPlayers + 1
    emit('newPlayer', { "id": request.sid } )
    emit('userConnectDisconnect', { 'clients': clients }, broadcast = True)

@socketio.on('disconnect')
def test_disconnect():
    global clients
    newClientes = list(filter( lambda client: client['id'] != request.sid, clients))
    clients = newClientes
    positionsClients.pop(request.sid) #Eliminar posiciones del usuarios desconectado
    emit('userDisconnect', {'id': request.sid}, broadcast = True)
    emit('userConnectDisconnect', { 'clients': clients }, broadcast = True)

@socketio.on('send-position')
def sendPosition(message):
    global clients
    idUser = request.sid
    newUser = list(filter( lambda client: client['id'] == idUser, clients)) #Buscar usuario en la lisya
    newClientes = clients
    if newUser[0]['intentos'] > 0:
        newClients = list(map(lambda user: actualizarUser(user, idUser, message["position"]), clients)) #Actualizar info del usuarios en la lista
    elif newUser[0]['intentos'] == 0 and newUser[0]['correctos'] < 9:
        emit('failed')
    clients = newClientes
    emit('userConnectDisconnect', { 'clients': clients }, broadcast = True)

def actualizarUser(user, idUser, position):
    if user['id'] == idUser:
        if position in positionsClients[idUser]:
            user['correctos'] = user['correctos'] + 1
            # user['positions'].remove(position)
            positionsClients[idUser].remove(position)
            if user['correctos'] == 9: emit('success')
        else:
            user['incorrectos'] = user['incorrectos'] + 1
        user['intentos'] = user['intentos'] - 1
    return user

def barcoFila(queue):
    x = random.randint(0,6)
    y1 = random.randint(0,4)
    y2 = y1+1
    y3 = y1+2
    queue.put([f"{x},{y1}", f"{x},{y2}", f"{x},{y3}"])


def barcoColumna(queue):
    y = random.randint(0,6)
    x1 = random.randint(0,4)
    x2 = x1+1
    x3 = x1+2
    queue.put([f"{x1},{y}", f"{x2},{y}", f"{x3},{y}"])


def createPositions():
    t1 = threading.Thread(name="fila1", target=barcoFila, args=(que,))
    t2 = threading.Thread(name="columna", target=barcoColumna, args=(que,))
    t3 = threading.Thread(name="fila2", target=barcoFila, args=(que,))
    # Ejecutar los hilos
    r1 = t1.start()
    r2 = t2.start()
    r3 = t3.start()
    # Esperar que todos los hilos terminen la ejecución
    t1.join()
    t2.join()
    t3.join()

    # Obtener la información de la cola FIFO con get()
    return que.get() + que.get() + que.get()


print(createPositions())

#Validar si main es el archivo que estoy ejecutando para dejarlo escuchando
if __name__ == '__main__':
  socketio.run(app)