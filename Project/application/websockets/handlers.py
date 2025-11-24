from flask_socketio import join_room, leave_room, send, SocketIO


# Função para registrar todos os handlers
def register_socketio_handlers(socketio: SocketIO):
    
    @socketio.on("join")
    def handle_join(data):
        room = data["room"]
        username = data["username"] # Em um sistema mais avançado, você usaria current_user aqui
        join_room(room)
        send(f"{username} entrou na sala.", room=room)


    @socketio.on("message")
    def handle_message(data):
        room = data["room"]
        username = data["username"]
        message = data["message"]
        send(f"{username}: {message}", room=room)


    @socketio.on("leave")
    def handle_leave(data):
        room = data["room"]
        username = data["username"]
        leave_room(room)
        send(f"{username} saiu da sala.", room=room)

