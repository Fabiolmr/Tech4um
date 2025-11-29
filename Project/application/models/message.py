from application.extensions import db

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.String(20))
    
    # Quem enviou?
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Para qual sala?
    forum_id = db.Column(db.String(10), db.ForeignKey('forums.id'))

    # Relacionamentos (opcional, mas ajuda)
    sender = db.relationship('User', backref='messages_sent')