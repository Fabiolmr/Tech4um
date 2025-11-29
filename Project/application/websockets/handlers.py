from flask import request
from flask_socketio import join_room, leave_room, send, emit, SocketIO
from flask_login import current_user
from application.extensions import online_users, db
from application.models.forum import Forum
from application.models.message import Message
from application.models.user import User
from datetime import datetime

user_sids = {}

room_users = {}

# PEGA LISTA DE PARTICIPANTES
def get_participantes_list(room_id):
    forum = Forum.query.get(room_id)
    if not forum:
        return []
    
    lista_exibicao = []
    
    #db_members = {m.username: m for m in forum.members}

    processed_usernames = set()  

    for member in forum.members:
        # Verifica se ele está online na sala AGORA
        is_online_in_room = False
        if room_id in room_users and member.username in room_users[room_id]:
            is_online_in_room = True

        lista_exibicao.append({
            "username": member.username,
            "online": is_online_in_room, 
            "is_member": True,
            "is_creator": (member.username == forum.creator)
        })
        processed_usernames.add(member.username)

    if room_id in room_users:
        for visitor_username in room_users[room_id]:
            # Se ainda não foi adicionado (ou seja, não é membro)
            if visitor_username not in processed_usernames:
                lista_exibicao.append({
                    "username": visitor_username,
                    "online": True, # Se está em room_users, com certeza está online
                    "is_member": False,
                    "is_creator": (visitor_username == forum.creator)
                })

    # VERIFICA SE É MEMBRO
    #for username in active_usernames:
    #    if username not in db_members: # Só adiciona se já não foi processado acima
    #        lista_exibicao.append({
    #            "username": username,
    #            "online": True, # Se está em active_usernames, com certeza está online
    #            "is_member": False,
    #            "is_creator": (username == forum.creator)
    #        })
#
    lista_exibicao.sort(key=lambda x: (not x['online'], x['username']))

    return lista_exibicao



# ==========================
#   ROTA COMUNICAÇÃO    
# ==========================

def register_socketio_handlers(socketio: SocketIO):
    #ROTA CONNECT
    @socketio.on("connect")
    def handle_connect():
        if current_user.is_authenticated:
            # Adiciona ID do usuário ao set global de online
            online_users.add(current_user.username)
            user_sids[current_user.username] = request.sid
            print(f"User {current_user.username} connected (SID: {request.sid})")


    #ROTA DISCONNECT        
    @socketio.on("disconnect")
    def handle_disconnect():
        if current_user.is_authenticated:
            online_users.discard(current_user.username)
            user_sids.pop(current_user.username, None)
            print(f"User {current_user.username} disconnected")

            for r_id, users_set in room_users.items():
                if current_user.username in users_set:
                    users_set.discard(current_user.username)
                    # Atualiza a lista visualmente para quem ficou na sala
                    emit("users_list", get_participantes_list(r_id), room=r_id)
       


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

            # ADICIONA À MEMÓRIA DA SALA (IMPORTANTE PARA A LISTA)
            if room_id not in room_users:
                room_users[room_id] = set()
            room_users[room_id].add(current_user.username)

            # CRIA MENSAGEM NOTIFICANDO ENTRADA
            #sys_msg_text = f"{current_user.username} entrou na sala."
        #
            #emit("message", {
            #    "user": "Sistema",
            #    "text": sys_msg_text,
            #    "time": datetime.now().strftime("%H:%M")
            #}, room=room_id)

            
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

        if room_id:
            leave_room(room_id)

            if room_id in room_users:
                room_users[room_id].discard(current_user.username)
            
            #sys_msg_text = f"{current_user.username} saiu da sala."
            #
            #emit("message", {
            #    "user": "Sistema",
            #    "text": sys_msg_text,
            #    "time": datetime.now().strftime("%H:%M")
            #}, room=room_id)
            
            # Atualiza lista (o usuário vai aparecer offline ou sair da lista)
            emit("users_list", get_participantes_list(room_id), room=room_id)


# ==========================
#   ROTA MENSAGEM
# ==========================


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