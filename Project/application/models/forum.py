#-----------CLASSE FÓRUM-------------
class Forum:
    def __init__(self, id, name, description, creator):
        self.id = id
        self.name = name
        self.description = description
        self.creator = creator
        self.participantes = [] #ARMAZENA PARTICIPANTES QUE ESTÃO ONLINE
        self.members = []   #ARMAZENA TODOS OS PARTICIPANTES DO FÓRUM
        self.messages = []

        self.add_member(creator)

    def add_participant(self, user):
        if not any(p.id == user.id for p in self.participantes):
                pass
        
    
    def add_member(self, username):
        if username not in self.members:
            self.members.append(username)


    def remove_member(self, username):
        if username in self.members:
            self.members.remove(username)