from flask import request
from flask_socketio import join_room, leave_room, send, emit, SocketIO
from flask_login import current_user
from application.extensions import rooms

# Inicialize o socketio com suporte às sessões
socketio = SocketIO(manage_session=True)

def register_socketio_handlers(socketio: SocketIO):

    def get_participantes_list(room_id):
        if room_id in rooms:
            return [
                {
                    "username": u['username'],
                    "online": u.get("online", False)
                }
                for u in rooms[room_id].participantes
            ]
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

            # BUSCA SE O USUÁRIO JÁ EXISTE NA LISTA GLOBAL
            usuario_existente = next((u for u in rooms[room].participantes if u['id'] == current_user.id), None)

            if usuario_existente:
                # Apenas atualiza o estado dele
                usuario_existente["sid"] = request.sid
                usuario_existente["online"] = True
                usuario_existente["in_room"] = True
            else:
                # Criar novo usuário global
                user_data = {
                    "id": current_user.id,
                    "username": current_user.username,
                    "sid": request.sid,
                    "online": True,
                    "in_room": True      # AGORA ESTÁ NA SALA
                }
                rooms[room].participantes.append(user_data)

            join_room(room)

            send(f"{username} entrou na sala.", room=room)

            # Envia somente quem está na sala
            emit("update_participants", {
                "users": [u for u in rooms[room].participantes if u["in_room"]]
            }, room=room)

            print(f"{username} entrou {room}")


    
    @socketio.on("leave")
    def handle_leave(data):
        room = data["room"]
        username = current_user.username

        if room in rooms:
            for u in rooms[room].participantes:
                if u["id"] == current_user.id:
                    u["in_room"] = False      # SAI DA SALA MAS CONTINUA ONLINE
                    break

            leave_room(room)
            send(f"{username} saiu da sala.", room=room)

            # Atualiza só quem está na sala
            emit("update_participants", {
                "users": [u for u in rooms[room].participantes if u["in_room"]]
            }, room=room)

            print(f"{username} saiu da sala {room}")



    @socketio.on("disconnect")
    def handle_disconnect():
        if current_user.is_authenticated:

            for room_id, forum in rooms.items():

                for u in forum.participantes:
                    if u["id"] == current_user.id:

                        u["online"] = False    # FICA OFFLINE
                        u["sid"] = None
                        u["in_room"] = False   # NÃO ESTÁ EM NENHUMA SALA
                        break

                leave_room(room_id)

                send(f"{current_user.username} saiu da sala.", room=room_id)

                emit("update_participants", {
                    "users": [u for u in forum.participantes if u["in_room"]]
                }, room=room_id)

                print(f"{current_user.username} desconectou da sala {room_id}")
                break




    @socketio.on("get_users")
    def get_users(data):
        room = data["room"]
        emit("users_list", rooms[room].participantes, to=request.sid)

           