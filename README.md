# **Tech4um – Plataforma de Fóruns em Tempo Real**

## 📌 Descrição Geral
O **Tech4um** é uma aplicação web de fóruns com comunicação em tempo real, permitindo que usuários criem e participem de salas de discussão sobre diversos temas.  

O projeto foi desenvolvido para avaliar a colaboração da equipe na construção de uma aplicação completa, integrando:

- **Frontend** moderno e responsivo  
- **Backend** com Flask e SQLAlchemy  
- **Comunicação em tempo real** usando Socket.IO  
- **Gerenciamento de usuários** com autenticação e perfis  

A aplicação oferece suporte a conversas públicas e privadas, criação de salas, gestão de membros e atualização dinâmica de participantes online.

---

## 🎯 Objetivo do Projeto
Construir uma plataforma funcional que permita:

1. **Autenticação de usuários** (login, cadastro e login via Google OAuth)  
2. **Visualização e criação de fóruns (salas)**  
3. **Troca de mensagens em tempo real** (públicas e privadas)  
4. **Gestão de membros** e navegação fluida entre salas  
5. **Edição de perfil**, upload de avatar e exclusão de conta  

---

## 🧩 Funcionalidades

### **1. Autenticação de Usuário**
- Cadastro com:
  - Nome de usuário único  
  - E-mail válido  
  - Senha segura (mínimo 8 caracteres, maiúsculas, minúsculas, números e caracteres especiais)  
- Login e logout  
- Login com **Google OAuth**  
- Perfil com avatar e dados do usuário  
- Edição de perfil e atualização em todas as salas  
- Exclusão permanente de conta  

### **2. Dashboard e Fóruns**
- Visualização de todos os fóruns disponíveis  
- Criação de novos fóruns (nome único + descrição opcional)  
- Entrar em fóruns existentes  
- Gestão de membros do fórum  
- Atualização em tempo real da lista de participantes  

### **3. Chat em Tempo Real**
- Envio de mensagens públicas dentro de cada fórum  
- Atualização instantânea via **WebSockets (Socket.IO)**  
- Lista de usuários online em tempo real  
- Suporte a múltiplas salas simultâneas  

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.10+**  
- **Flask** – Framework web  
- **Flask-Login** – Autenticação de usuários  
- **Flask-SocketIO** – Comunicação em tempo real  
- **SQLAlchemy** – ORM para banco de dados  
- **Cloudinary** – Upload e hospedagem de avatares
- **GRavatar** - para gerar avatar caso o usuário não coloque foto 
- **HTML, CSS, JavaScript** – Frontend  
- **Tailwind CSS** – Estilização rápida e responsiva  
- **Flask-Dance** – Login via Google OAuth  
- **SQLite / Neon (PostgreSQL)** – Banco de dados  

---

## Criar e ativar ambiente virtual

python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate    # Windows

## pip install -r requirements.txt

## Executar a aplicação
python run.py

Acesse: http://localhost:5000/

O servidor WebSocket será executado junto com a aplicação

Autores

Fabio

Ana

Carlos

## 💡 Observações

Inicialmente, o sistema salvava os dados na memória do computador,
depois foi implementado o banco de dados PostgreSQL com o Neon.

Consegui subir o projeto: https://tech4um-eucx.onrender.com/
