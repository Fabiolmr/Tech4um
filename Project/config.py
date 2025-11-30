import os
from dotenv import load_dotenv

#carrega dados senciveis do .env
load_dotenv()

#REGISTRO DE DADOS SENSÍVEIS 

class Config:
    # O segundo parâmetro do getenv é um valor padrão caso a variável não exista no .env
    SECRET_KEY = os.getenv("SECRET_KEY", "chave_padrao_insegura_para_dev")
    
    # Configuração do Banco de Dados
    # Garante que o caminho seja absoluto para evitar erros com o SQLite
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Se não houver no .env, usa o sqlite padrão
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", f"sqlite:///{os.path.join(BASE_DIR, 'users.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
