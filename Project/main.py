#executar este arquivo para teste local
#Obs: o login com o google não está 100% implementado
#mais

from application import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app, debug=True)