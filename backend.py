from flask import Flask, render_template
import psycopg2

app = Flask (__name__)

host = "127.0.0.1"
name = "atividade"
user = "postgres"
password = "postgres"

def conexao_database():
    conn = None
    try:
        conn = psycopg2.connect(host=host, database=name, user=user, password=password)
    except psycopg2.Error as e:
        print (f"Problema ao conectar ao banco: {e}")
    return conn

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

@app.route('/')
def mostrar_database():
    conn = conexao_database()
    if conn:
        tabela = "atividade"
        novo_nome_colunas = ["ID", "Descrição", "Data de criação", "Data prevista", "Data encerramento", "Situação"]
        colunas, dados = leitura_database(conn, tabela, novo_nome_colunas)
        conn.close()
        if colunas and dados:
            return render_template('page.html', colunas=colunas, dados=dados)
        else:
            return "Erro ao bucar dados"
    else:
        return "Erro na conexão com banco"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)