from flask_socketio import join_room, leave_room, send, emit, SocketIO
from flask_login import current_user
from application.extensions import rooms

# Inicialize o socketio com suporte às sessões
socketio = SocketIO(manage_session=True)

def register_socketio_handlers(socketio: SocketIO):

    def get_participantes_list(room_id):
        if room_id in rooms:
            return [{"username": u['username']} for u in rooms[room_id].participantes]
        return []

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
        username = current_user.username

        if not room or not username:
            return
        
        if room in rooms:
            user_data = {"id": current_user.id, "username": current_user.username}

            if not any(u['id'] == user_data['id'] for u in rooms[room].participantes):
                rooms[room].participantes.append(user_data)

            join_room(room)
            send(f"{username} entrou na sala.", room=room)
            emit("update_participants", {"users": get_participantes_list(room)}, room=room)
            print(f"{username} entrou {room}")

    
    @socketio.on("leave")
    def handle_leave(data):
        room = data["room"]
        username = current_user.username

        if room in rooms:
            rooms[room].participantes = [u for u in rooms[room].participantes if u['id'] != current_user.id]
            leave_room(room)
            send(f"{username} saiu da sala.", room=room)
            emit("update_participants", {"users": get_participantes_list(room)}, room=room)
            print(f"{username} saiu da sala {room}")
