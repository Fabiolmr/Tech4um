from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from datetime import datetime, timedelta

# --------------------------------------------------------------------
# MODELOS (BACK-END)
# --------------------------------------------------------------------

class User:
    def __init__(self, username, karma=0):
        self.username = username
        self.karma = karma
        self.messages = []  # para notificações futuramente

class Subreddit:
    def __init__(self, name, title=None, description=""):
        self.name = name
        self.title = title or name
        self.description = description

    def url(self):
        return f"/r/{self.name}"

class Post:
    _id_counter = 1

    def __init__(self, title, author: User, subreddit: Subreddit, content="", created_at=None, score=0, comments=0):
        self.id = Post._id_counter
        Post._id_counter += 1
        self.title = title
        self.author = author
        self.subreddit = subreddit
        self.content = content
        self.created_at = created_at or datetime.utcnow()
        self.score = score
        self.comments = comments

    def age_str(self):
        delta = datetime.utcnow() - self.created_at
        if delta < timedelta(minutes=1):
            return "just now"
        if delta < timedelta(hours=1):
            return f"{int(delta.seconds/60)}m"
        if delta < timedelta(days=1):
            return f"{int(delta.seconds/3600)}h"
        return f"{delta.days}d"

    def upvote(self): self.score += 1
    def downvote(self): self.score -= 1


# --------------------------------------------------------------------
# DADOS FAKE
# --------------------------------------------------------------------

alice = User("alice", karma=2345)
bob = User("bob_the_builder", karma=413)

python_sr = Subreddit("python", "Python", "Tudo sobre Python")
programming_sr = Subreddit("programming", "Programming", "Discussão geral sobre programação")
webdev_sr = Subreddit("webdev", "WebDev", "Desenvolvimento web")

subreddits = [python_sr, programming_sr, webdev_sr]

posts = [
    Post("Clone de Reddit em Python (OOP + Flask)", alice, python_sr, score=123, comments=12),
    Post("Qual sua piada de programação favorita?", bob, programming_sr, score=42, comments=7),
    Post("Entendendo GIL e async", alice, python_sr, score=87, comments=30),
]


# --------------------------------------------------------------------
# FLASK
# --------------------------------------------------------------------
app = Flask(__name__)


# --------------------------------------------------------------------
# TEMPLATE (FRONT-END)
# --------------------------------------------------------------------
TEMPLATE = """
<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8">
  <title>Mini Reddit</title>
  <style>
    body{font-family:Arial;background:#eee;margin:0}
    .topbar{background:#fff;padding:14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #ddd}
    .search input{padding:8px;border-radius:8px;width:100%;border:1px solid #ccc}
  </style>
</head>
<body>

  <div class="topbar">
    <div class="logo">mini <span style="color:#ff4500">reddit</span></div>

    <!-- BARRA DE BUSCA -->
    <div class="search" style="position:relative; width:300px;">
        <input 
            type="text" 
            id="searchInput" 
            placeholder="Pesquisar salas..."
            onkeyup="filterRooms()"
        >

        <div id="searchResults" 
             style="position:absolute; top:40px; left:0; right:0; background:#fff; border:1px solid #ddd; border-radius:8px; display:none; max-height:150px; overflow-y:auto; z-index:10;">
        </div>
    </div>

    <!-- LOGIN -->
    <button onclick="location.href='/login'">Login</button>
  </div>

<script>
    const rooms = [
        {% for sr in subreddits %}"{{sr.name}}",{% endfor %}
    ];

    function filterRooms() {
        const input = document.getElementById("searchInput").value.toLowerCase();
        const resultsDiv = document.getElementById("searchResults");

        resultsDiv.innerHTML = "";

        if (!input.trim()) {
            resultsDiv.style.display = "none";
            return;
        }

        const filtrados = rooms.filter(r => r.toLowerCase().includes(input));

        if (filtrados.length === 0) {
            resultsDiv.style.display = "none";
            return;
        }

        filtrados.forEach(room => {
            const item = document.createElement("div");
            item.textContent = "r/" + room;
            item.style.padding = "10px";
            item.style.cursor = "pointer";
            item.onclick = () => window.location.href = "/search?room=" + room;

            item.onmouseover = () => item.style.background = "#eee";
            item.onmouseout  = () => item.style.background = "#fff";

            resultsDiv.appendChild(item);
        });

        resultsDiv.style.display = "block";
    }
</script>



  <div style="padding:20px;">
    <h2>Feed</h2>

    {% if bob.messages %}
      <div style="background:#fffae6;padding:10px;border:1px solid #f0d000;border-radius:8px;margin-bottom:12px;">
        <strong>Você tem {{bob.messages|length}} mensagens privadas!</strong>
      </div>
    {% endif %}

    {% for post in posts %}
      <div style="background:#fff;padding:12px;margin-bottom:12px;border-radius:8px;border:1px solid #ddd;">
        <h3>{{post.title}}</h3>
        <p>Postado em <strong>r/{{post.subreddit.name}}</strong></p>
        <p>{{post.score}} votos • {{post.comments}} comentários</p>

        <form action="/vote/{{post.id}}" method="post">
          <button name="type" value="up">▲ Upvote</button>
          <button name="type" value="down">▼ Downvote</button>
        </form>
      </div>
    {% endfor %}
  </div>

</body>
</html>
"""


# --------------------------------------------------------------------
# ROTAS BACK-END (FUNCIONALIDADES)
# --------------------------------------------------------------------

@app.route("/")
def home():
    return render_template_string(
        TEMPLATE, 
        posts=posts, 
        subreddits=subreddits,
        bob=bob           # <--- CORREÇÃO AQUI
    )

@app.route("/vote/<int:post_id>", methods=["POST"])
def vote(post_id):
    p = next((x for x in posts if x.id == post_id), None)
    if not p:
        return "Post não encontrado", 404

    if request.form.get("type") == "up":
        p.upvote()
    else:
        p.downvote()

    return redirect(url_for("home"))

@app.route("/search")
def search():
    room = request.args.get("room")
    if not room:
        return redirect("/")

    filtrados = [p for p in posts if p.subreddit.name == room]

    return render_template_string(
        TEMPLATE,
        posts=filtrados,
        subreddits=subreddits,
        bob=bob     # <--- CORREÇÃO AQUI
    )

@app.route("/forums")
def forums():
    return jsonify([{"name": sr.name, "title": sr.title} for sr in subreddits])

@app.route("/login")
def login():
    return "<h2>Página de Login</h2><p><a href='/'>Voltar</a></p>"


# --------------------------------------------------------------------
# EXECUTAR
# --------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=8080)
