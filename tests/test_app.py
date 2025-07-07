import pytest
from backend import app, conexao_database  # substitua por seu nome real do arquivo, se necessário
from flask import session

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

#1
def test_login_success(client):
    response = client.post('/login', data={
        'email': 'andreifranzon2001@hotmail.com',
        'senha': 'andrei'
    }, follow_redirects=True)

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'ok'
    assert 'token' in data
#2
def test_login_falha(client):
    response = client.post('/login', data={
        'email': 'usuarioinvalido@email.com',
        'senha': 'senhaerrada'
    }, follow_redirects=True)

    assert response.status_code == 401 or response.status_code == 400
    data = response.get_json()
    assert data['status'] == 'erro' or 'message' in data
#3
def test_login_retorno_json(client):
    response = client.post('/login', data={
        'email': 'andreifranzon2001@hotmail.com',
        'senha': 'andrei'
    }, follow_redirects=True)

    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'token' in data
    assert 'email' in data
    assert data['status'] == 'ok'
#4
def test_cadastro_usuario(client):
    # Envia a requisição POST para a rota de cadastro
    response = client.post('/cadastro', data={
        'email': 'novousuario4@email.com',
        'senha': 'senhadificil',
        'nome': 'Novo Usuário'
    }, follow_redirects=True)

    # Verifique se o código de status é 200, indicando sucesso na operação
    assert response.status_code == 200

    # Verifique se o redirecionamento para a página index ocorreu
    assert response.request.url.endswith('/index')

# Fixture para criar o app Flask
@pytest.fixture(scope='module')
def client():
    # Configuração do app para testes
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Banco de dados em memória para testes
    app.config['MAIL_SUPPRESS_SEND'] = True  # Desativa o envio real de e-mails durante os testes

    # Usamos um cliente de teste para enviar requisições à aplicação
    with app.test_client() as client:
        yield client
#5
import pytest
from backend import app  # Substitua pelo nome do seu arquivo real

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

#5
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

#6
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
def test_deletar_atividade(client):
    # Envia uma requisição GET para deletar a atividade com ID 15
    response = client.get('/deletar/59')

    # Verifica se a resposta redireciona corretamente após deletar
    assert response.status_code == 302  # Redirecionamento esperado após exclusão
    assert response.location == '/read'  # Verifica se redireciona para a lista de atividades
#10
def test_editar_atividade(client):
    # Primeiro, cria uma nova atividade para depois editá-la
    response_create = client.post('/create', data={
        'descricao': 'Atividade Original',
        'data_criacao': '2025-01-01',
        'data_prevista': '2025-01-10',
        'data_encerramento': '2025-01-11',
        'situacao': 'Em Planejamento'
    }, follow_redirects=True)

    assert response_create.status_code == 200

    # Suponha que a nova atividade tenha sido salva com ID 1 (ajuste se necessário)
    # Agora edita essa atividade
    response_edit = client.post('/editar/33', data={
        'descricao': 'Atividade Editada',
        'data_criacao': '2025-01-01',
        'data_prevista': '2025-01-15',
        'data_encerramento': '2025-01-20',
        'situacao': 'Em Andamento'
    }, follow_redirects=True)

    assert response_edit.status_code == 200
    assert b'Atividade Editada' in response_edit.data
#11
def test_editar_e_deletar_atividade(client):
    # Edita a atividade com ID 32
    response_edit = client.post('/editar/58', data={
        'descricao': 'Atividade Editada para Exclusão',
        'data_criacao': '2025-01-05',
        'data_prevista': '2025-01-12',
        'data_encerramento': '2025-01-20',
        'situacao': 'Concluída'
    }, follow_redirects=True)

    # Verifica se a edição foi bem-sucedida
    assert response_edit.status_code == 200
    
    # Verifica se a string "Atividade Editada para Exclusão" está presente no HTML retornado
    html = response_edit.data.decode('utf-8')  # Converte os bytes para string
    assert 'Atividade Editada para Exclusão' in html  # Verifica se a descrição editada está na resposta HTML

#12
def test_filtrar_atividades_por_data_criacao(client):
    # Envia uma requisição GET para filtrar as atividades pela data de criação
    response = client.get('/read?data_criacao_filtro=2025-05-10')
    
    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200
    
    # Verifica se os dados retornados estão corretos, por exemplo, que a data filtrada aparece
    assert b'2025-05-10' in response.data
#13
def test_filtrar_atividades_por_data_prevista(client):
    # Envia uma requisição GET para filtrar as atividades pela data prevista
    response = client.get('/read?data_prevista_filtro=2025-06-10')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se a data que deveria estar filtrada aparece na resposta
    assert b'2025-06-10' in response.data
#14
def test_filtrar_atividades_por_data_encerramento(client):
    # Envia uma requisição GET para filtrar as atividades pela data de encerramento
    response = client.get('/read?data_encerramento_filtro=2025-07-10')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se a data que deveria estar filtrada aparece na resposta
    assert b'2025-07-10' in response.data
#15
def test_filtrar_atividades_por_situacao(client):
    # Envia uma requisição GET para filtrar as atividades pela situação "Em Andamento"
    response = client.get('/read?situacao=Em Andamento')

    # Verifica se a resposta foi bem-sucedida
    assert response.status_code == 200

    # Imprime a resposta para depuração
    print(response.data)

    # Verifica se a situação filtrada "Em Andamento" aparece na resposta
    assert b'Em Andamento' in response.data
#16
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
#17
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

#18
def test_criacao_atividade_campos_vazios(client):
    resposta = client.post('/create', data={})
    
    # Verifica se houve recarregamento do formulário (sem redirecionamento)
    assert resposta.status_code == 400 or resposta.status_code == 200

    # Verifica que não houve redirecionamento para /read ou /mostrar_database
    assert b"Adicionar Atividade" in resposta.data

#19
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

#20
def test_edicao_atividade_sem_mudanca(client):
    # Suponha que a atividade com ID 32 já existe no banco de dados
    id_atividade = 88

    # Dados da atividade atuais (sem modificações)
    dados_atividade = {
        'descricao': 'Atividade Original',  # Suponha que essa seja a descrição original da atividade
        'data_criacao': '2025-01-05',  # Mantém a mesma data de criação
        'data_prevista': '2025-01-12',  # Mantém a mesma data prevista
        'data_encerramento': '2025-01-20',  # Mantém a mesma data de encerramento
        'situacao': 'Concluída'  # Mantém a mesma situação
    }

    # Realiza a requisição POST para editar a atividade com os mesmos dados
    resposta_edicao = client.post(f'/editar/{id_atividade}', data=dados_atividade, follow_redirects=True)

    # Verifica se a edição foi bem-sucedida (status 200)
    assert resposta_edicao.status_code == 200

    # Verifica se a descrição da atividade aparece no HTML da resposta
    html = resposta_edicao.data.decode('utf-8')
    assert 'Atividade Original' in html  # Verifica se a descrição original está na página
    assert '2025-01-05' in html  # Verifica se a data de criação não foi alterada
    assert '2025-01-12' in html  # Verifica se a data prevista não foi alterada
    assert '2025-01-20' in html  # Verifica se a data de encerramento não foi alterada
    assert 'Concluída' in html  # Verifica se a situação não foi alterada