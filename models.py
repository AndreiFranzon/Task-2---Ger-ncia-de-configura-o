from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    email = Column(String(150))
    senha = Column(Text)

class Atividade(Base):
    __tablename__ = 'atividade'
    id = Column(Integer, primary_key=True)
    descricao = Column(Text)
    data_criacao = Column(Date)
    data_prevista = Column(Date)
    data_encerramento = Column(Date)
    situacao = Column(String(50))

class Teste(Base):
    __tablename__ = 'teste'
    id = Column(Integer, primary_key=True)
    nome = Column(String(12))

class Teste2(Base):
    __tablename__ = 'teste2'
    id = Column(Integer, primary_key=True)
    nome = Column(String(50))
