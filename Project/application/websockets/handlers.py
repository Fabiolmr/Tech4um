from flask import request
from flask_socketio import join_room, leave_room, send, emit, SocketIO
from flask_login import current_user
from application.extensions import online_users
#from application.models.user import User
from datetime import datetime

# PEGA LISTA DE PARTICIPANTES
def get_participantes_list(room_id):
        if room_id in rooms:
            forum = rooms[room_id]
            lista_exibicao = []

            # VERIFICA SE É MEMBRO
            for member_name in forum.members:
                user_data = next((u for u in forum.participantes if u['username'] == member_name), None)  
                is_active = (user_data is not None) and user_data.get('in_room', False)
                
                lista_exibicao.append({
                    "username": member_name,
                    "online": is_active,
                    "is_member": True,
                    "is_creator": (member_name == forum.creator)
                })
            members_set = set(forum.members)
            # VERIFICA SE É VISITANTE
            for p in forum.participantes:
                if p['username'] not in members_set and p.get('in_room', False):
                    lista_exibicao.append({
                        "username": p['username'],
                        "online": True,
                        "is_member": False, # Visitante
                        "is_creator": (p['username'] == forum.creator)
                    })

            lista_exibicao.sort(key=lambda x: (not x['online'], x['username']))

            return lista_exibicao
            
        return []


# ==========================
#   ROTA COMUNICAÇÃO    
# ==========================

def register_socketio_handlers(socketio: SocketIO):
    #ROTA CONNECT
    @socketio.on("connect")
    def handle_connect():
        if current_user.is_authenticated:
            # Adiciona ID do usuário ao set global de online
            online_users.add(current_user.id)
            print(f"User {current_user.username} connected (Global)")
            # Atualiza a lista para todo mundo

    #ROTA DISCONNECT        
    @socketio.on("disconnect")
    def handle_disconnect():
        if current_user.is_authenticated:
            print(f"User {current_user.username} disconnected (Global)")

            # VÊ SE O PARTICIPANTE TÁ NA SALA
            for room_id, forum in rooms.items():
                for u in forum.participantes:
                    if u['id'] == current_user.id:
                        if u.get('sid') == request.sid:
                            if u.get('in_room'):
                                # CRIA MENSAGEM AVIZANDO QUE SAIU
                                system_msg = {
                                    "user": "Sistema",
                                    "text": f"{current_user.username} saiu da sala."
                                }
                                # ADICIONA MENSAGEM
                                forum.messages.append(system_msg)
                                send(system_msg, room=room_id)    
                                u['in_room'] = False
                                u['online'] = False
                                u['sid'] = None
                                
                                #AVISA OS OUTROS PARTICIPANTES ONLINE SOBRE A NOVA LISTA
                                emit("users_list", get_participantes_list(room_id), room=room_id)
            # DISCARTA USUÁRIO QUE SAIU
            online_users.discard(current_user.id)

    #ROTA JOIN
    @socketio.on("join")
    def handle_join(data):
        room = data.get("room")
        # BLOQUEIA USUÁRIOS NÃO AUTENTICAOD  E QUE NÃO EXISTA FÓRUM
        if not current_user.is_authenticated or not room:
            return

        username = current_user.username
        
        if room in rooms:
            # BUSCA SE O USUÁRIO JÁ EXISTE NA LISTA GLOBAL
            rooms[room].participantes = [u for u in rooms[room].participantes if u['id'] != current_user.id]

            # Criar novo usuário global
            user_data = {
            "id": current_user.id,
            "username": username,
            "sid": request.sid,
            "online": True,
            "in_room": True
            }
            rooms[room].participantes.append(user_data)

            join_room(room)

            # CRIA MENSAGEM NOTIFICANDO ENTRADA
            system_msg = {
                "user": "Sistema",
                "text": f"{username} entrou na sala."
            }

            rooms[room].messages.append(system_msg)
            #ENVIA MENSAGEM
            send(system_msg, room=room)

            # NOTIFICA A COMUNICAÇÃO DA NOVA LISTA
            emit("users_list", get_participantes_list(room), room=room)

            print(f"{username} entrou {room}")

        else:
            # NOTIFICA CASO DÊ ALGUM ERRO
            emit("error_redirect", {"url": "/"})


    #ROTA DE SAÍDA    
    @socketio.on("leave")
    def handle_leave(data):
        if not current_user.is_authenticated:
            return

        room = data.get("room")
        username = current_user.username

        if room in rooms:
            for u in rooms[room].participantes:
                if u["id"] == current_user.id:
                    u["in_room"] = False 
                    break

            leave_room(room)

            system_msg = {
                "user": "Sistema",
                "text": f"{username} saiu da sala."
            }

            rooms[room].messages.append(system_msg)
            send(system_msg, room=room)
         
            emit("users_list", get_participantes_list(room), room=room)
            print(f"{username} saiu da sala {room}")


# ==========================
#   ROTA MENSAGEM
# ==========================


  # ROTA MEMSAGEM PRIVADA
    #OBS.: O usuário digita: "@nome_exato mensagem"
    #       onde nome_exato = nome da pessoa igual a que tá salva e mensagem é a mensagem a ser mandada no privado

    @socketio.on("private_message")
    def handle_private_message(data):
        if not current_user.is_authenticated:
            return

        room_id = data.get("room")
        # USUÁRIO ALVO
        recipient_username = data.get("recipient")
        message = data.get("message")
        
        if not room_id or not recipient_username or not message:
            return
            
        if room_id not in rooms:
            return

        username = current_user.username
        current_time = datetime.now().strftime("%H:%M")

        # Procura o usuário alvo na lista de participantes daquela sala
        target_user_in_room = next((u for u in rooms[room_id].participantes if u['username'] == recipient_username), None)

        # Se encontrou o usuário e ele tem um ID de sessão (sid)
        if target_user_in_room and target_user_in_room.get('sid'):
            # Emite o evento 'private_message' para o sid do alvo
            emit("private_message", {
                "user": username,
                "text": message,
                "recipient": recipient_username,
                "time": current_time,
                "is_sent": False
            }, to=target_user_in_room['sid'])
            
            print(f"[Privado] {username} para {recipient_username}: {message}")
        else:
            # Avisar quem enviou que o usuário não foi encontrado
            emit("private_message", {
                "user": "Sistema",
                "text": f"Usuário {recipient_username} não encontrado ou offline nesta sala.",
                "recipient": username,
                "time": current_time
            }, to=request.sid)


    #ROTA MENSAGEM PÚBLICA
    @socketio.on("message")
    def handle_message(data):
        if not current_user.is_authenticated:
            return
        
        room = data["room"]
        if room not in rooms:
            return

        # MENSAGEM RECEBE VALOR
        message = data.get("message")
        username = current_user.username
        current_time = datetime.now().strftime("%H:%M")

        #CRIA NOVA MEMSAGEM OBJETO
        msg_data = {
            "user": username,
            "text": message,
            "time": current_time
        }
        #ADICIONA NA LISTA
        rooms[room].messages.append(msg_data)
        #AVISA COMUNICAÇÃO SOBRE MUDANÇA NA LISTA MENSAGEM
        emit("message", msg_data, room=room)
        print(f"{username} disse: {message}")

