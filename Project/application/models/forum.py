#-----------CLASSE FÓRUM-------------
class Forum:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.participantes = [] #ARMAZENA PARTICIPANTES
        self.messages = []


    def add_participant(self, user):
        if not any(p.id == user.id for p in self.participantes):
                self.participantes.append(user)
        