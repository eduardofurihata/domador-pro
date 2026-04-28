SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

NOTION_SCRIPT := ./scripts/notion-sync.py
NOTION_TOKEN_FILE := $(HOME)/.config/notion-sync/.env
NOTION_STATE := .notion-sync.json
NOTION_DEFAULT_SCOPE := docs

# Override scope: make dev:notion-push SCOPE=docs/marketing/brand
SCOPE ?= $(NOTION_DEFAULT_SCOPE)

# Sobrescreve mesmo com mudança remota: make dev:notion-push FORCE=1
ifdef FORCE
FORCE_FLAG := --force
else
FORCE_FLAG :=
endif

# Garante que uv está acessível (instalado em ~/.local/bin)
NOTION_PATH := PATH="$(HOME)/.local/bin:$$PATH"

.PHONY: help \
        ensure-uv ensure-token-file ensure-init \
        notion-setup notion-check \
        notion-init \
        dev\:notion-push dev\:notion-pull dev\:notion-status \
        notion-push notion-pull notion-status

help: ## Lista comandos
	@printf "Notion sync — comandos disponíveis\n\n"
	@printf "  \033[36m%-22s\033[0m %s\n" \
	  "help"               "Lista comandos" \
	  "notion-setup"       "Instala uv (se faltar) e cria estrutura de config" \
	  "notion-check"       "Verifica ambiente sem aplicar nada" \
	  "notion-init URL=…"  "Bootstrap: define raiz do Notion" \
	  "dev:notion-push"    "Envia local → Notion (default: docs/)" \
	  "dev:notion-pull"    "Traz Notion → local (default: docs/)" \
	  "dev:notion-status"  "Diff dry-run em ambos sentidos (default: docs/)"
	@printf "\nVariáveis úteis:\n"
	@printf "  SCOPE=docs/foo            limita push/pull a um subpath\n"
	@printf "  FORCE=1                   ignora detecção de conflito\n\n"
	@printf "Primeira vez: make notion-setup && edite ~/.config/notion-sync/.env && make notion-init URL=...\n"

# ─── ensures (idempotentes) ───────────────────────────────────────────

ensure-uv:
	@if ! command -v uv >/dev/null 2>&1 && ! [ -x "$(HOME)/.local/bin/uv" ]; then \
		printf "→ uv não encontrado. Instalando…\n"; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	fi

ensure-token-file:
	@mkdir -p $(HOME)/.config/notion-sync
	@chmod 700 $(HOME)/.config/notion-sync
	@if [ ! -f $(NOTION_TOKEN_FILE) ]; then \
		echo "NOTION_TOKEN=" > $(NOTION_TOKEN_FILE); \
		chmod 600 $(NOTION_TOKEN_FILE); \
		printf "\n❌ Token não estava configurado.\n\n"; \
		printf "  Criei o arquivo vazio em: %s\n" "$(NOTION_TOKEN_FILE)"; \
		printf "  Edite e adicione:        NOTION_TOKEN=ntn_…\n"; \
		printf "  Pegue o token em:        https://www.notion.so/profile/integrations\n\n"; \
		exit 1; \
	fi

ensure-init:
	@test -f $(NOTION_STATE) || { \
		printf "\n❌ Repo ainda não inicializado.\n\n"; \
		printf "  Rode: make notion-init URL=https://www.notion.so/...\n\n"; \
		exit 1; \
	}

# ─── setup explícito ──────────────────────────────────────────────────

notion-setup: ensure-uv ## Instala uv (se faltar) e cria estrutura de config
	@mkdir -p $(HOME)/.config/notion-sync
	@chmod 700 $(HOME)/.config/notion-sync
	@if [ ! -f $(NOTION_TOKEN_FILE) ]; then \
		echo "NOTION_TOKEN=" > $(NOTION_TOKEN_FILE); \
		chmod 600 $(NOTION_TOKEN_FILE); \
		printf "→ Criado %s vazio. Edite e adicione: NOTION_TOKEN=ntn_…\n" "$(NOTION_TOKEN_FILE)"; \
	else \
		printf "✓ %s já existe\n" "$(NOTION_TOKEN_FILE)"; \
	fi
	@printf "✓ Setup concluído. Próximo: make notion-init URL=…\n"

notion-check: ensure-uv ensure-token-file ensure-init ## Verifica ambiente sem aplicar nada
	@grep -qE '^NOTION_TOKEN=ntn_' $(NOTION_TOKEN_FILE) || { \
		printf "❌ NOTION_TOKEN inválido em %s. Edite o arquivo.\n" "$(NOTION_TOKEN_FILE)"; \
		exit 1; \
	}
	@printf "✓ Ambiente OK (uv + token + state)\n"

# ─── bootstrap ────────────────────────────────────────────────────────

notion-init: ensure-uv ensure-token-file ## Bootstrap: make notion-init URL=https://www.notion.so/...
ifndef URL
	$(error Use: make notion-init URL=<url-da-pagina-Notion>)
endif
	@$(NOTION_PATH) $(NOTION_SCRIPT) init "$(URL)" --as agencia-domapro

# ─── operações principais ────────────────────────────────────────────

dev\:notion-push: notion-check ## Envia local → Notion (default: docs/)
	@$(NOTION_PATH) $(NOTION_SCRIPT) push $(SCOPE) $(FORCE_FLAG)

dev\:notion-pull: notion-check ## Traz Notion → local (default: docs/)
	@$(NOTION_PATH) $(NOTION_SCRIPT) pull $(SCOPE) $(FORCE_FLAG)

dev\:notion-status: notion-check ## Diff dry-run em ambos sentidos (default: docs/)
	@$(NOTION_PATH) $(NOTION_SCRIPT) status $(SCOPE)

# Aliases sem o "dev:" pra quem prefere
notion-push: dev\:notion-push
notion-pull: dev\:notion-pull
notion-status: dev\:notion-status
