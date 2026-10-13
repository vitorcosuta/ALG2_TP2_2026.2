VENV   := .venv
PYTHON := $(VENV)/bin/python

# Analisa apenas os diretórios que já existem
SRC_DIRS := $(wildcard src tests)

.DEFAULT_GOAL := help
.PHONY: help venv install lint format-check typecheck complexity test check fix clean

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  make %-14s %s\n", $$1, $$2}'

$(PYTHON):
	python3 -m venv $(VENV)

venv: $(PYTHON) ## Cria o ambiente virtual em .venv

install: $(PYTHON) ## Instala as dependências de desenvolvimento
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements-dev.txt

lint: ## Ruff: erros, imports e bugs comuns
	$(PYTHON) -m ruff check .

format-check: ## Ruff: verifica a formatação sem alterar arquivos
	$(PYTHON) -m ruff format --check .

typecheck: ## Mypy: verificação de tipos (modo strict)
ifneq ($(SRC_DIRS),)
	$(PYTHON) -m mypy $(SRC_DIRS)
else
	@echo "mypy: nenhum diretório src/ ou tests/ encontrado, pulando."
endif

complexity: ## Radon: complexidade ciclomática e manutenibilidade
ifneq ($(SRC_DIRS),)
	$(PYTHON) -m radon cc $(SRC_DIRS) -s -a
	$(PYTHON) -m radon mi $(SRC_DIRS) -s
else
	@echo "radon: nenhum diretório src/ ou tests/ encontrado, pulando."
endif

test: ## Pytest: testes unitários
	@$(PYTHON) -m pytest; status=$$?; \
		if [ $$status -eq 5 ]; then echo "pytest: nenhum teste encontrado."; exit 0; fi; \
		exit $$status

check: lint format-check typecheck complexity test ## Roda todas as verificações

fix: ## Aplica correções automáticas do Ruff e formata o código
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

clean: ## Remove caches das ferramentas
	rm -rf .ruff_cache .mypy_cache .pytest_cache
	find . -type d -name __pycache__ -not -path './$(VENV)/*' -exec rm -rf {} +
