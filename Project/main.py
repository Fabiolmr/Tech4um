#executar este arquivo para teste local
#Obs: o login com o google não está 100% implementado

from application import create_app, socketio
from application.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Banco de dados conectato e tabelas criadas")

if __name__ == "__main__":
    socketio.run(app, debug=True)