from flask import request
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

        #----------- LÓGICA PARA MENSAGEM PRIVADA----------#
        #OBS.: O usuário digita: "@nome_exato mensagem"
        #       onde nome_exato = nome da pessoa igual a que tá salva e mensagem é a mensagem a ser mandada no privado
        if message.startswith("@"):
            partes = message.split(" ", 1)

            if len(partes) > 1:
                target_username = partes[0][1:]
                msg_text = partes[1]

                target_user = next((u for u in rooms[room].participantes if u['username'] == target_username), None)

                if target_user and 'sid' in target_user:

                    private_msg = f"[Privado de {username}]: {msg_text}"
                    emit("message", private_msg, to=target_user['sid'])

                    emit("message", f"[Privado para {target_username}]: {msg_text}", to=request.sid)

                    return
            else:
                emit("message", "Usuário não encontrado ou offline.", to=request.sid)
                return
            
        #----------- LÓGICA PARA MENSAGEM PÚBLICA ----------#

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
            user_data = {
                "id": current_user.id,
                "username": current_user.username,
                "sid": request.sid
            }

            #if not any(u['id'] == user_data['id'] for u in rooms[room].participantes):
            rooms[room].participantes = [u for u in rooms[room].participantes if u['id'] != current_user.id]
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


    @socketio.on("disconnect")
    def handle_disconnect():
        if current_user.is_authenticated:

            for room_id, forum in rooms.items():  
                if any(u['id'] == current_user.id for u in forum.participantes):     
                    forum.participantes = [u for u in forum.participantes if u['id'] != current_user.id]  
                    leave_room(room_id)
                    
                    send(f"{current_user.username} saiu da sala.", room=room_id)
                    emit("update_participants", {"users": get_participantes_list(room_id)}, room=room_id)
                    print(f"{current_user.username} desconectou (aba fechada) da sala {room_id}")
                    break