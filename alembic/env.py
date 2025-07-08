from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ─────────────────────────────────────────────────────────────
# 1) Garante que a raiz do projeto (onde está models.py) esteja no PYTHONPATH
# ‑‑ isso permite: from models import Base
# ─────────────────────────────────────────────────────────────
sys.path.append(os.path.abspath(os.getcwd()))

# 2) Importa o Base (que contém metadata das tabelas)
from models import Base  # ajuste o import se models.py estiver em outra pasta

# ─────────────────────────────────────────────────────────────
# Alembic config
# ─────────────────────────────────────────────────────────────
config = context.config

# Se existir um .ini com logging configurado, carrega
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 3) Metadados que o Alembic usará para autogenerate
target_metadata = Base.metadata

# 4) Se houver variável de ambiente DATABASE_URL, substitui a URL do .ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)


# ─────────────────────────────────────────────────────────────
# Funções padrão do template Alembic (offline / online)
# ─────────────────────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Executa as migrações em modo "offline".
    Gera o SQL sem precisar conectar ao banco.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Executa as migrações em modo "online".
    Cria um Engine, abre conexão e roda as migrações.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# ─────────────────────────────────────────────────────────────
# Decide se roda offline ou online
# ─────────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
