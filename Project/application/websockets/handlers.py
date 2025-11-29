from flask import request
from flask_socketio import join_room, leave_room, send, emit, SocketIO
from flask_login import current_user
from application.extensions import online_users, db
from application.models.forum import Forum
from application.models.message import Message
from application.models.user import User
from datetime import datetime

user_sids = {}

# PEGA LISTA DE PARTICIPANTES
def get_participantes_list(room_id):
    forum = Forum.query.get(room_id)
    if not forum:
        return []
    
    lista_exibicao = []

    # VERIFICA SE É MEMBRO
    for member in forum.members:
        is_online = member.username in online_users
        
        lista_exibicao.append({
            "username": member.username,
            "online": is_online,
            "is_member": True,
            "is_creator": (member.username == forum.creator)
        })

    lista_exibicao.sort(key=lambda x: (not x['online'], x['username']))

    return lista_exibicao


    #        members_set = set(forum.members)
    #        # VERIFICA SE É VISITANTE
    #        for p in forum.participantes:
    #            if p['username'] not in members_set and p.get('in_room', False):
    #                lista_exibicao.append({
    #                    "username": p['username'],
    #                    "online": True,
    #                    "is_member": False, # Visitante
    #                    "is_creator": (p['username'] == forum.creator)
    #                })
#
    #        lista_exibicao.sort(key=lambda x: (not x['online'], x['username']))
#
    #        return lista_exibicao
    #        
    #    return []


# ==========================
#   ROTA COMUNICAÇÃO    
# ==========================

def register_socketio_handlers(socketio: SocketIO):
    #ROTA CONNECT
    @socketio.on("connect")
    def handle_connect():
        if current_user.is_authenticated:
            # Adiciona ID do usuário ao set global de online
            user_sids[current_user.username] = request.sid
            print(f"User {current_user.username} connected (SID: {request.sid})")


    #ROTA DISCONNECT        
    @socketio.on("disconnect")
    def handle_disconnect():
        if current_user.is_authenticated:
            online_users.discard(current_user.username)
            user_sids.pop(current_user.username, None)
            print(f"User {current_user.username} disconnected")

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
        room_id = data.get("room")
        # BLOQUEIA USUÁRIOS NÃO AUTENTICAOD  E QUE NÃO EXISTA FÓRUM
        if not current_user.is_authenticated or not room_id:
            return

        forum = Forum.query.get(room_id)

        if forum:
            join_room(room_id)

            username = current_user.username

            # CRIA MENSAGEM NOTIFICANDO ENTRADA
            sys_msg_text = f"{current_user.username} entrou na sala."
        
            emit("message", {
                "user": "Sistema",
                "text": sys_msg_text,
                "time": datetime.now().strftime("%H:%M")
            }, room=room_id)

            
            emit("users_list", get_participantes_list(room_id), room=room_id)

            #ENVIA MENSAGEM

            # NOTIFICA A COMUNICAÇÃO DA NOVA LISTA

            #print(f"{username} entrou {room}")

        else:
            # NOTIFICA CASO DÊ ALGUM ERRO
            emit("error_redirect", {"url": "/"})


    #ROTA DE SAÍDA    
    @socketio.on("leave")
    def handle_leave(data):
        if not current_user.is_authenticated:
            return

        room_id = data.get("room")
        username = current_user.username

        if room_id:
            leave_room(room_id)
            
            sys_msg_text = f"{current_user.username} saiu da sala."
            
            emit("message", {
                "user": "Sistema",
                "text": sys_msg_text,
                "time": datetime.now().strftime("%H:%M")
            }, room=room_id)
            
            # Atualiza lista (o usuário vai aparecer offline ou sair da lista)
            emit("users_list", get_participantes_list(room_id), room=room_id)


# ==========================
#   ROTA MENSAGEM
# ==========================


  # ROTA MEMSAGEM PRIVADA
    #OBS.: O usuário digita: "@nome_exato mensagem"
    #       onde nome_exato = nome da pessoa igual a que tá salva e mensagem é a mensagem a ser mandada no privado

    #@socketio.on("private_message")
    #def handle_private_message(data):
    #    if not current_user.is_authenticated:
    #        return
#
    #    room_id = data.get("room")
    #    # USUÁRIO ALVO
    #    recipient_username = data.get("recipient")
    #    message = data.get("message")
    #    
    #    if not room_id or not recipient_username or not message:
    #        return
    #        
    #    if room_id not in rooms:
    #        return
#
    #    username = current_user.username
    #    current_time = datetime.now().strftime("%H:%M")
#
    #    # Procura o usuário alvo na lista de participantes daquela sala
    #    target_user_in_room = next((u for u in rooms[room_id].participantes if u['username'] == recipient_username), None)
#
    #    # Se encontrou o usuário e ele tem um ID de sessão (sid)
    #    if target_user_in_room and target_user_in_room.get('sid'):
    #        # Emite o evento 'private_message' para o sid do alvo
    #        emit("private_message", {
    #            "user": username,
    #            "text": message,
    #            "recipient": recipient_username,
    #            "time": current_time,
    #            "is_sent": False
    #        }, to=target_user_in_room['sid'])
    #        
    #        print(f"[Privado] {username} para {recipient_username}: {message}")
    #    else:
    #        # Avisar quem enviou que o usuário não foi encontrado
    #        emit("private_message", {
    #            "user": "Sistema",
    #            "text": f"Usuário {recipient_username} não encontrado ou offline nesta sala.",
    #            "recipient": username,
    #            "time": current_time
    #        }, to=request.sid)


    #ROTA MENSAGEM PÚBLICA
    @socketio.on("message")
    def handle_message(data):
        if not current_user.is_authenticated:
            return
        room_id = data.get("room")
        text = data.get("message")
        
        # Validação básica
        if not room_id or not text:
            return

        # Verifica se a sala existe no banco
        forum = Forum.query.get(room_id)
        if not forum:
            return

        current_time = datetime.now().strftime("%H:%M")
        # 1. SALVA NO BANCO DE DADOS
        try:
            new_msg = Message(
                text=text,
                user_id=current_user.id,
                forum_id=room_id,
                timestamp=current_time
            )
            db.session.add(new_msg)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao salvar mensagem: {e}")
            return

        # 2. EMITE PARA O SOCKET (TEMPO REAL)
        current_time = datetime.now().strftime("%H:%M")
        msg_data = {
            "user": current_user.username,
            "text": text,
            "time": current_time
        }
        
        emit("message", msg_data, room=room_id)
        print(f"Msg DB [{room_id}] {current_user.username}: {text}")


    @socketio.on("private_message")
    def handle_private_message(data):
        if not current_user.is_authenticated:
            return

        recipient_username = data.get("recipient")
        message = data.get("message")
        current_time = datetime.now().strftime("%H:%M")

        # Busca o SID do destinatário no nosso dicionário user_sids
        recipient_sid = user_sids.get(recipient_username)

        if recipient_sid:
            # Envia APENAS para o socket do destinatário
            emit("private_message", {
                "user": current_user.username,
                "text": message,
                "recipient": recipient_username,
                "time": current_time,
                "is_sent": False
            }, to=recipient_sid)
        else:
            # Avisa o remetente que o usuário não está conectado
            emit("private_message", {
                "user": "Sistema",
                "text": f"Usuário {recipient_username} está offline.",
                "recipient": recipient_username,
                "time": current_time
            }, to=request.sid)