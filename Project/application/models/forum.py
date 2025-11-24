#-----------CLASSE FÓRUM-------------
class Forum:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.participantes = [] #ARMAZENA PARTICIPANTES

    def add_participant(self, user):
        if not any(p.id == user.id for p in self.participantes):
                self.participantes.append(user)

def get_all_forums():
    # Dados simulados para a Homepage
    return [
        Forum(1, "Python Developers", "Discussão sobre a linguagem Python."),
        Forum(2, "Flask & WebSockets", "Dúvidas sobre o backend e tempo real."),
        Forum(3, "Chat Geral", "Sala para conversas aleatórias."),
    ]