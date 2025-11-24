class Forum:
    def __init__(self, id, name, description):
        self.id = id
        self.name = name
        self.description = description
        self.participantes = []

def get_all_forums():
    """Retorna a lista de todos os fóruns disponíveis."""
    # *Em um projeto real, isso faria uma query no Banco de Dados*
    
    # Dados simulados para a Homepage
    return [
        Forum(1, "Python Developers", "Discussão sobre a linguagem Python."),
        Forum(2, "Flask & WebSockets", "Dúvidas sobre o backend e tempo real."),
        Forum(3, "Chat Geral", "Sala para conversas aleatórias."),
    ]