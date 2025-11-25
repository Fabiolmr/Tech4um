from flask_socketio import join_room, leave_room, send, SocketIO
from flask_login import current_user

# Inicialize o socketio com suporte às sessões
socketio = SocketIO(manage_session=True)

def register_socketio_handlers(socketio: SocketIO):

    @socketio.on("join")
    def handle_join(data):
        room = data["room"]
        username = current_user.username  # agora pega do login real
        join_room(room)
        send(f"{username} entrou na sala.", room=room)

    @socketio.on("message")
    def handle_message(data):
        room = data["room"]
        message = data["message"]
        username = current_user.username
        send(f"{username}: {message}", room=room)

    @socketio.on("leave")
    def handle_leave(data):
        room = data["room"]
        username = current_user.username
        leave_room(room)
        send(f"{username} saiu da sala.", room=room)
