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
   #created_at = db.Column(db.DateTime, default=datetime.utcnow)

        #self.add_member(creator)
    messages = db.relationship('Message', backref='forum', lazy=True)

    members = db.relationship('User', secondary=forum_members, lazy='subquery',
        backref=db.backref('forums', lazy=True))

    #def add_participant(self, user):
    #    if not any(p.id == user.id for p in self.participantes):
    #            pass
    #    
    #
    #def add_member(self, username):
    #    if username not in self.members:
    #        self.members.append(username)
#
#
    #def remove_member(self, username):
    #    if username in self.members:
    #        self.members.remove(username)