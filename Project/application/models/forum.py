from application.extensions import db

forum_members = db.Table('forum_members',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('forum_id', db.String(10), db.ForeignKey('forums.id'), primary_key=True)
)


#-----------CLASSE FÓRUM-------------
class Forum(db.Model):
    __tablename__ = 'forums'
    id = db.Column(db.String(10), primary_key=True) # Código da sala (ex: "XJ9Z")
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    creator = db.Column(db.String(150)) # Poderia ser relacionamento, mas vamos manter simples por enquanto


    messages = db.relationship('Message', backref='forum', lazy=True)

    members = db.relationship('User', secondary=forum_members, lazy='subquery',
        backref=db.backref('forums', lazy=True))
