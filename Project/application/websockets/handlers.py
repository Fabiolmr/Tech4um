from flask_socketio import join_room, leave_room, send, SocketIO
from flask_login import current_user
from application.extensions import rooms

# Inicialize o socketio com suporte às sessões
socketio = SocketIO(manage_session=True)

def register_socketio_handlers(socketio: SocketIO):

    @socketio.on("message")
    def handle_message(data):
        room = data["room"]

        if room not in rooms:
            return

        message = data["message"]
        username = current_user.username

        msg_content = f"{username}: {message}"

        rooms[room].messages.append(msg_content)

        send(msg_content, room=room)
        print(f"{username} disse: {msg_content}")


    @socketio.on("join")
    def handle_join(data):
        room = data["room"]
        username = current_user.username  # agora pega do login real

        if not room or not username:
            return
        if room not in rooms:
            return
        
        join_room(room)
        send(f"{username} entrou na sala.", room=room)
        print(f"{username} entrou {room}")

    
    @socketio.on("leave")
    def handle_leave(data):
        room = data["room"]
        username = current_user.username
        leave_room(room)
        send(f"{username} saiu da sala.", room=room)
        print(f"{username} saiu da sala {room}")
