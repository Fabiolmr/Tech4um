#executar este arquivo para teste local

import eventlet
eventlet.monkey_patch()

import os

from application import create_app, socketio
from application.extensions import db

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

app = create_app()

with app.app_context():
    db.create_all()
    print("Banco de dados conectato e tabelas criadas")

if __name__ == "__main__":
    socketio.run(app, debug=True)