import pytest

from app import config
from app.data.loader import carregar

# As planilhas não vão para o Git: sem elas, os testes são pulados em vez de falhar.
if not (config.ARQ_BASE.exists() and config.ARQ_CNPJ.exists()):
    pytest.skip("Planilhas da Aditive não encontradas em data/", allow_module_level=True)


@pytest.fixture(scope="session")
def base():
    return carregar()
