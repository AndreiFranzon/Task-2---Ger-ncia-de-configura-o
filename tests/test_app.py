import pytest
import uuid
from backend import app, conexao_database  # substitua por seu nome real do arquivo, se necessário
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

created_user = {}

#1
def test_login_falha(client):
    response = client.post('/login', data={
        'email': 'usuarioinvalido@email.com',
        'senha': 'senhaerrada'
    }, follow_redirects=True)

    assert response.status_code == 401 or response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'erro' or 'message' in data

#2
def test_cadastro_usuario(client):
    email = "emailteste@teste.com"
    senha = "senha123"

    resp = client.post(
        "/cadastro",
        data={"nome": "Usuário Teste", "email": email, "senha": senha},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/index")

    # pega o ID no banco
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    assert row, "Usuário não encontrado"
    user_id = row[0]

    # grava em variável global
    created_user["id"] = user_id

#3
def test_login_retorno_json(client):
    response = client.post('/login', data={
        'email': 'emailteste@teste.com',
        'senha': 'senha123'
    }, follow_redirects=True)

    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'token' in data
    assert 'email' in data
    assert data['status'] == 'ok'

#4
def test_login_success(client):
    response = client.post('/login', data={
        'email': 'emailteste@teste.com',
        'senha': 'senha123'
    }, follow_redirects=True)

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'token' in data

#5
def test_deletar_usuario(client):
    # garante que o cadastro rodou antes
    assert "id" in created_user, "Usuário ainda não foi criado!"
    user_id = created_user["id"]

    resp_del = client.post(f"/usuarios/deletar/{user_id}", follow_redirects=False)
    assert resp_del.status_code == 302
    assert resp_del.headers["Location"].startswith("/usuarios")

    # confirma remoção
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM usuarios WHERE id = %s", (user_id,))
    assert cur.fetchone() is None, "Usuário não foi deletado!"
    cur.close(); conn.close()

#6
def test_cadastro_incompleto_nome(client):
    # Envia a requisição POST para a rota de cadastro com apenas o nome
    response = client.post('/cadastro', data={
        'nome': 'Novo Usuário'
    }, follow_redirects=True)

    # Verifica se a resposta é 400, pois a validação de dados deve falhar
    assert response.status_code == 400  # Espera um erro de solicitação inválida

    # Decodifica a resposta de bytes para string
    response_data = response.data.decode('utf-8')

    # Verifica se a resposta HTML contém a mensagem de erro
    assert 'Bad Request' in response_data  # Verifica a mensagem de erro padrão

#7
def test_pagina_cadastro(client):
    # Envia uma requisição GET para acessar a página de cadastro
    response = client.get('/create')
    assert response.status_code == 200
    # Verifique se o título "Adicionar Atividade" está presente
    assert b'Adicionar Atividade' in response.data

#8
def test_leitura_atividades(client):
    # Envia uma requisição GET para a página de leitura de atividades
    response = client.get('/read')
    assert response.status_code == 200

    # Verifica se o título "Dados da tabela" está na página
    assert b'Dados da tabela' in response.data

#9
def test_criar_atividade(client, mocker):
    # Mock de envio de e-mail (não envia e-mail real durante o teste)
    mock_send_message = mocker.patch('smtplib.SMTP.send_message', autospec=True)

    # Dados para enviar pelo formulário de cadastro
    dados = {
        'descricao': 'Atividade Teste',
        'data_criacao': '2025-05-10',
        'data_prevista': '2025-06-10',
        'data_encerramento': '2025-07-10',
        'situacao': 'Em andamento',
        'email_usuario': 'teste@exemplo.com'
    }

    # Envia uma requisição POST para criar a atividade
    response = client.post('/create', data=dados)

    # Verifica se a resposta é um redirecionamento para a página de leitura de dados (o que indica sucesso)
    assert response.status_code == 302
    assert response.location.endswith('/read')

    # Verifica se a atividade foi inserida no banco
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT * FROM atividade WHERE descricao = %s", ('Atividade Teste',))
    atividade = cur.fetchone()
    conn.close()
    assert atividade is not None  # Verifica se a atividade foi inserida no banco

    # Verifica se o e-mail foi "enviado" (mocked)
    mock_send_message.assert_called_once()  # Verifica se o método de envio de e-mail foi chamado uma vez

#10 
def test_edicao_atividade_sem_mudanca(client):
    # Primeiro, pega o id da atividade criada (que deve existir por causa do teste anterior)
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT id FROM atividade WHERE descricao = %s ORDER BY id DESC LIMIT 1", ('Atividade Teste',))
    resultado = cur.fetchone()
    cur.close()
    conn.close()

    assert resultado is not None, "Atividade para edição não encontrada"
    id_atividade = resultado[0]

    # Dados iguais aos da criação, sem modificação
    dados_atividade = {
        'descricao': 'Atividade Teste',
        'data_criacao': '2025-05-10',
        'data_prevista': '2025-06-10',
        'data_encerramento': '2025-07-10',
        'situacao': 'Em andamento',
        'email_usuario': 'teste@exemplo.com'  # mantenha mesmo email se necessário
    }

    resposta_edicao = client.post(f'/editar/{id_atividade}', data=dados_atividade, follow_redirects=True)

    assert resposta_edicao.status_code == 200

    html = resposta_edicao.data.decode('utf-8')
    # Confirma que a descrição e datas continuam iguais no HTML retornado
    assert 'Atividade Teste' in html
    assert '2025-05-10' in html
    assert '2025-06-10' in html
    assert '2025-07-10' in html
    assert 'Em andamento' in html

#11
def test_filtrar_atividades_por_situacao(client):
    response = client.get('/read?situacao=Em Andamento')
    assert response.status_code == 200

    # comparação sem diferenciar maiúsc/minúsc
    assert b'em andamento' in response.data.lower()

#12
def test_editar_atividade(client):
    # Busca a atividade que foi criada anteriormente
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT id FROM atividade WHERE descricao = %s ORDER BY id DESC LIMIT 1", ('Atividade Teste',))
    resultado = cur.fetchone()
    cur.close()
    conn.close()

    assert resultado is not None, "Atividade para edição não encontrada"
    id_atividade = resultado[0]

    # Dados atualizados
    dados_edicao = {
        'descricao': 'Atividade Editada',
        'data_criacao': '2025-05-10',
        'data_prevista': '2025-06-15',
        'data_encerramento': '2025-07-20',
        'situacao': 'Concluída',
        'email_usuario': 'teste@exemplo.com'
    }

    response_edit = client.post(f'/editar/{id_atividade}', data=dados_edicao, follow_redirects=True)

    assert response_edit.status_code == 200

    html = response_edit.data.decode('utf-8')
    assert 'Atividade Editada' in html
    assert '2025-06-15' in html
    assert '2025-07-20' in html
    assert 'Concluída' in html

#13
def test_deletar_atividade(client):
    """
    Deleta a atividade criada nos testes anteriores e confirma:
    – status 302 (redirect)
    – redirecionamento para /read
    – remoção definitiva no banco
    """

    # 1) Descobre o ID da atividade que já existe
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM atividade WHERE descricao = %s ORDER BY id DESC LIMIT 1",
        ('Atividade Editada',)        # descrição usada no teste de criação
    )
    res = cur.fetchone()
    assert res is not None, "Atividade para deleção não encontrada"
    id_atividade = res[0]
    cur.close()
    conn.close()

    # 2) Executa a deleção (ajuste p/ POST se sua rota exigir)
    resp_del = client.get(f"/deletar/{id_atividade}", follow_redirects=False)

    # 3) Valida redirect
    assert resp_del.status_code == 302
    assert resp_del.headers["Location"].endswith("/read")

    # 4) Garante que sumiu do banco
    conn = conexao_database()
    cur = conn.cursor()
    cur.execute("SELECT id FROM atividade WHERE id = %s", (id_atividade,))
    assert cur.fetchone() is None, "Atividade não foi removida do banco"
    cur.close()
    conn.close()

#14
def test_filtrar_atividades_por_data_criacao(client):
    # Envia uma requisição GET para filtrar as atividades pela data de criação
    response = client.get('/read?data_criacao_filtro=2025-05-10')
    
    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200
    
    # Verifica se os dados retornados estão corretos, por exemplo, que a data filtrada aparece
    assert b'2025-05-10' in response.data

#15
def test_filtrar_atividades_por_data_prevista(client):
    # Envia uma requisição GET para filtrar as atividades pela data prevista
    response = client.get('/read?data_prevista_filtro=2025-06-10')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se a data que deveria estar filtrada aparece na resposta
    assert b'2025-06-10' in response.data
#16
def test_filtrar_atividades_por_data_encerramento(client):
    # Envia uma requisição GET para filtrar as atividades pela data de encerramento
    response = client.get('/read?data_encerramento_filtro=2025-07-10')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se a data que deveria estar filtrada aparece na resposta
    assert b'2025-07-10' in response.data

#17
def test_filtrar_atividades_com_todos_os_filtros(client):
    # Envia uma requisição GET para filtrar as atividades com todos os filtros
    response = client.get('/read?situacao=Em andamento&data_criacao_filtro=2025-05-10&data_prevista_filtro=2025-06-10' \
    '&data_encerramento_filtro=2025-07-10')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se todos os filtros aplicados estão na resposta
    assert b'Em andamento' in response.data
    assert b'2025-05-10' in response.data
    assert b'2025-06-10' in response.data
    assert b'2025-07-10' in response.data

from io import BytesIO
#18
def test_gerar_pdf(client):
    # Envia uma requisição GET para gerar o PDF
    response = client.get('/pdf_tabela')  # O endpoint de geração de PDF no seu código
    
    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200
    
    # Verifica se a resposta tem o cabeçalho correto para um arquivo PDF
    assert response.content_type == 'application/pdf'
    
    # Verifica se a resposta não está vazia
    assert len(response.data) > 0
    
    pdf_content = BytesIO(response.data)

    print("PDF gerado com sucesso!")

#19
def test_criacao_atividade_campos_vazios(client):
    resposta = client.post('/create', data={})
    
    # Verifica se houve recarregamento do formulário (sem redirecionamento)
    assert resposta.status_code == 400 or resposta.status_code == 200

    # Verifica que não houve redirecionamento para /read ou /mostrar_database
    assert b"Adicionar Atividade" in resposta.data

#20
def test_exclusao_atividade_inexistente(client):
    # Suponha que o ID 99999 não existe na base de dados
    id_invalido = 99999
    resposta = client.delete(f'/deletar/{id_invalido}')  # Usando DELETE em vez de POST

    # Verifica se o status code é 404, indicando que a atividade não foi encontrada
    assert resposta.status_code == 404

    # Converte resposta.data de bytes para string e verifica se a mensagem personalizada de erro está presente
    html = resposta.data.decode('utf-8')

    # Verifica se a mensagem personalizada "Atividade não encontrada" está presente na resposta
    assert "Atividade não encontrada" in html  # Mensagem personalizada de erro