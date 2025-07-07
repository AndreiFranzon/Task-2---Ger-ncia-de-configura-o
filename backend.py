from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, make_response, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import psycopg2, io, uuid, smtplib, os

app = Flask (__name__)

host = "127.0.0.1"
name = "atividade"
user = "postgres"
password = "postgres"

#Conexão com o banco
def conexao_database():
    conn = None
    try:
        conn = psycopg2.connect(host=host, port=5432, database=name, user=user, password=password)
    except psycopg2.Error as e:
        print (f"Problema ao conectar ao banco: {e}")
    return conn

#Config email

load_dotenv()

#Envio de email
def enviar_email(destinatario, nome_usuario):
    remetente = os.getenv('EMAIL_SENDER')
    senha = os.getenv('APP_PASSWORD')  # <-- coloque sua senha de aplicativo aqui
    assunto = 'Confirmação de cadastro'

    corpo = f"""
    Olá {nome_usuario},

    Sua conta foi criada com sucesso no nosso sistema.

    Obrigado por se cadastrar!

    Atenciosamente,
    Equipe do Sistema
    """

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(mensagem)
        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def email_cadastro(destinatario):
    remetente = os.getenv('EMAIL_SENDER')
    senha = os.getenv('APP_PASSWORD')       
    assunto = 'Cadastro de atividade confirmado'

    corpo = f"""
    Olá,

    Sua atividade foi cadastrada com sucesso!

    Atenciosamente,
    Equipe do Sistema
    """

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(mensagem)
        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def email_edit(destinatario):
    remetente = os.getenv('EMAIL_SENDER')
    senha = os.getenv('APP_PASSWORD')
    assunto = 'Edição de atividade confirmado'

    corpo = f"""
    Olá,

    Você editou a atividade com sucesso!

    Atenciosamente,
    Equipe do Sistema
    """

    mensagem = MIMEMultipart()
    mensagem['From'] = remetente
    mensagem['To'] = destinatario
    mensagem['Subject'] = assunto
    mensagem.attach(MIMEText(corpo, 'plain', 'utf-8'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha)
            servidor.send_message(mensagem)
        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")  

#Login & Cadastro
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        conn = conexao_database()
        cur = conn.cursor()
        cur.execute("SELECT senha FROM usuarios WHERE email =%s", (email,))
        resultado = cur.fetchone()
        cur.close()
        conn.close()

        if resultado and check_password_hash(resultado[0], senha):
            token = str(uuid.uuid4())
            return jsonify({'status': 'ok', 'token': token, 'email': email})
        else:
            return jsonify({'status': 'erro', 'mensagem': 'Credenciais inválidas'}), 401

    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        conn = conexao_database()
        cur = conn.cursor()

        cur.execute("SELECT * FROM usuarios WHERE email =%s", (email,))
        usuario_existente = cur.fetchone()

        if usuario_existente:
            cur.close()
            conn.close()
            return redirect(url_for('cadastro'))

        senha_hash = generate_password_hash(senha)

        cur.execute("""
                INSERT INTO usuarios (nome, email, senha)
                VALUES (%s, %s, %s)
            """, (nome, email, senha_hash))
        conn.commit()
        cur.close()
        conn.close()

        enviar_email(email,nome)

        return redirect(url_for('index'))

    return render_template('cadastro.html')

#Gerenciamento de usuários

@app.route('/usuarios')
def listar_usuarios():
    conn = conexao_database()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, nome, email FROM usuarios ORDER BY id")
        usuarios = cur.fetchall()
    except psycopg2.Error as e:
        print(f"Erro ao buscar usuários: {e}")
        usuarios = []
    finally:
        cur.close()
        conn.close()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/deletar/<int:id>', methods=['POST'])
def deletar_usuario(id):
    conn = conexao_database()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        conn.commit()
        if cur.rowcount == 0:
            mensagem = 'Usuário não encontrado.'
        else:
            mensagem = 'Usuário deletado com sucesso.'
    except psycopg2.Error as e:
        mensagem = f'Erro ao deletar usuário: {e}'
    finally:
        cur.close()
        conn.close()
    # Redireciona para listar usuários passando a mensagem via query string
    return redirect(url_for('listar_usuarios', msg=mensagem))


#Crud
def leitura_database(conn, tabela, nome_colunas=None):
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {tabela}")
        colunas = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        if nome_colunas and len(nome_colunas) == len (colunas):
            colunas_exibicao = nome_colunas
        else:
            colunas_exibicao = colunas
        
        return colunas_exibicao, dados
    except psycopg2.Error as e:
        print(f"Problema ao buscar dados: {e}")
        return None, None
    finally:
        cur.close()

@app.route('/read')
def mostrar_atividades():
    situacao = request.args.get('situacao')
    data_criacao_filtro = request.args.get('data_criacao_filtro')
    data_prevista_filtro = request.args.get('data_prevista_filtro')
    data_encerramento_filtro = request.args.get('data_encerramento_filtro')
    conn = conexao_database()
    
    if conn:
        tabela = "atividade"
        novo_nome_colunas = ["ID", "Descrição", "Data de criação", "Data prevista", "Data encerramento", "Situação"]
        cur = conn.cursor()
        
        query = "SELECT * FROM atividade WHERE 1=1"
        params = []

        if situacao and situacao.lower() != 'todos':
            query += " AND LOWER(TRIM(situacao)) = LOWER(TRIM(%s))"
            params.append(situacao)
        
        if data_criacao_filtro:
            query += " AND data_criacao = %s"
            params.append(data_criacao_filtro)

        if data_prevista_filtro:
            query += " AND data_prevista = %s"
            params.append(data_prevista_filtro)

        if data_encerramento_filtro:
            query += " AND data_encerramento = %s"
            params.append(data_encerramento_filtro)
        
        cur.execute(query, tuple(params))
        colunas = [desc[0] for desc in cur.description]
        dados = cur.fetchall()
        cur.close()
        conn.close()

        return render_template(
            'page.html',
             colunas=novo_nome_colunas,
             dados=dados, situacao_atual=situacao,
             data_criacao_filtro=data_criacao_filtro,
             data_prevista_filtro=data_prevista_filtro,
             data_encerramento_filtro=data_encerramento_filtro
             )
    else:
        return "Erro na conexão com banco"

@app.route('/create', methods=['GET', 'POST'])
def criar_atividade():
    if request.method == 'POST':
        descricao = request.form.get('descricao', '').strip()
        data_criacao = request.form.get('data_criacao', '').strip()
        data_prevista = request.form.get('data_prevista', '').strip()
        data_encerramento = request.form.get('data_encerramento', '').strip()
        situacao = request.form.get('situacao', '').strip()
        email_usuario = request.form.get('email_usuario', '').strip()

        erros = {}
        if not descricao:
            erros['descricao'] = 'Descrição é obrigatória.'
        if not data_criacao:
            erros['data_criacao'] = 'Data de criação é obrigatória.'
        if not data_prevista:
            erros['data_prevista'] = 'Data prevista é obrigatória.'
        if not data_encerramento:
            erros['data_encerramento'] = 'Data de encerramento é obrigatória.'
        if not situacao:
            erros['situacao'] = 'Situação é obrigatória.'

        if erros:
            return render_template('form.html', erros=erros), 400

        conn = conexao_database()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO atividade (descricao, data_criacao, data_prevista, data_encerramento, situacao)
            VALUES (%s, %s, %s, %s, %s)
        """, (descricao, data_criacao, data_prevista, data_encerramento, situacao))
        conn.commit()
        cur.close()
        conn.close()

        if email_usuario:
            email_cadastro(email_usuario)

        return redirect(url_for('mostrar_atividades'))
    return render_template('form.html')


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_atividade(id):
    conn = conexao_database()
    cur = conn.cursor()
    if request.method == 'POST':
        descricao = request.form['descricao']
        data_criacao = request.form['data_criacao']
        data_prevista = request.form['data_prevista']
        data_encerramento = request.form['data_encerramento']
        situacao = request.form['situacao']
        cur.execute("""
    UPDATE atividade SET descricao=%s, data_criacao=%s, data_prevista=%s, data_encerramento=%s, situacao=%s WHERE id=%s
""", (descricao, data_criacao, data_prevista, data_encerramento, situacao, id))
        conn.commit()
        cur.close()
        conn.close()

        email_usuario = request.form.get('email_usuario')

        if email_usuario:
            email_edit(email_usuario)

        return redirect(url_for('mostrar_atividades'))
    else:
        cur.execute("SELECT * FROM atividade WHERE id = %s", (id,))
        atividade = cur.fetchone()
        cur.close()
        conn.close()
        return render_template('form.html', atividade=atividade)
    
@app.route('/deletar/<int:id>', methods=['GET', 'DELETE'])
def deletar_atividade(id):
    conn = conexao_database()
    cur = conn.cursor()

    # Tenta deletar a atividade
    cur.execute("DELETE FROM atividade WHERE id = %s", (id,))
    conn.commit()

    # Verifica se a atividade foi realmente excluída
    if cur.rowcount == 0:  # Nenhuma linha foi afetada, ou seja, a atividade não existe
        cur.close()
        conn.close()
        return "Atividade não encontrada", 404

    # Fecha a conexão com o banco
    cur.close()
    conn.close()

    # Redireciona para a página de exibição das atividades
    return redirect(url_for('mostrar_atividades'))


#Gerar pdfs
@app.route('/pdf_tabela')
def pdf_tabela():
    conn = conexao_database()

    tabela = "atividade"
    nome_colunas = ['ID', 'Descrição', 'Data de criação', 'Data prevista', 'Data de encerramento', 'Situação']
    colunas, dados = leitura_database(conn, tabela, nome_colunas)
    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    largura, altura = letter
    largura_colunas = [20, 70, 100, 85, 135, 150]

    y = altura - 50
    x_inicial = 50
    x = x_inicial

    for i, coluna in enumerate(colunas):
        pdf.drawString(x, y, coluna)
        x += largura_colunas[i]
    y -= 20

    for linha in dados:
        x = x_inicial
        for i, item in enumerate(linha):
            pdf.drawString(x, y, str(item))
            x += largura_colunas[i]
        y -=20
        if y < 50:
            pdf.showPage()
            y = altura - 50

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="atividades.pdf", mimetype='application/pdf')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)