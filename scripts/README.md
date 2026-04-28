# notion-sync

Sync bidirecional manual entre arquivos markdown do repo e páginas do Notion.

## Como funciona

Mental model: igual `git push/pull`, mas pra Notion.

- Você decide o sentido a cada execução (`push` ou `pull`)
- Hierarquia de pastas vira hierarquia de páginas (profundidade infinita)
- `README.md` de uma pasta vira o conteúdo da página da pasta
- Outros `.md` viram páginas filhas
- Mapeamento `arquivo ↔ page_id` fica em `.notion-sync.json` (commitado no repo)
- Token fica em `~/.config/notion-sync/.env` (NÃO commitado)

## Uso (via Makefile)

```bash
make help                              # lista comandos
make dev:notion-push                   # docs → Notion (default)
make dev:notion-pull                   # Notion → docs
make dev:notion-status                 # diff dry-run em ambos sentidos

make dev:notion-push SCOPE=docs/marketing/brand   # subpath
make dev:notion-push FORCE=1                       # ignora detecção de conflito

make notion-setup                      # idempotente: instala uv + cria estrutura
make notion-init URL=https://...       # bootstrap (só primeira vez)
```

`make notion-check` roda automaticamente como pré-requisito de push/pull.

Aliases curtos sem `dev:` também funcionam: `make notion-push`, `make notion-pull`, `make notion-status`.

## Setup primeira vez (já feito uma vez no repo)

1. **Cria integration no Notion**: https://www.notion.so/profile/integrations
2. **Compartilha página parent** com a integration (`...` no Notion → Connections)
3. **Salva token**:
   ```bash
   make notion-setup
   # edita ~/.config/notion-sync/.env e cola NOTION_TOKEN=ntn_...
   ```
4. **Bootstrap**:
   ```bash
   make notion-init URL=https://www.notion.so/Sync-...
   ```
   (cria página `agencia-domapro` dentro da `Sync` automaticamente via `--as`)

## Política de conflito

A detecção compara hash do arquivo local e `last_edited_time` do Notion contra o
último sync gravado em `.notion-sync.json`.

- **`push`**: se o lado Notion mudou desde o último sync → pula com aviso. Use
  `FORCE=1` pra sobrescrever.
- **`pull`**: se o local mudou desde o último sync → pula com aviso. Use
  `FORCE=1` pra sobrescrever.

`pull` também checa **round-trip equivalence**: se o local md → blocks → md é
igual ao que o Notion devolveria agora, pula sem reescrever (preserva sintaxe
markdown rica como links relativos).

Não há resolução de conflito merge. É last-write-wins quando você usa `FORCE=1`,
ou pula e te avisa pra resolver manualmente.

## O que é sincronizado

- Tudo dentro do `local_root` (default: `.` raiz do repo) que tenha `.md` em
  algum nível, **filtrado pelo SCOPE** do Makefile (default: `docs`)
- Pastas hidden (`.git`, `.foo`) são puladas
- Build/cache padrão: `node_modules`, `__pycache__`, `.venv`, `dist`, `build`,
  `target`, `.pytest_cache`, etc. são pulados
- Pastas que não tenham nenhum `.md` em qualquer nível são puladas (ex:
  `scripts/` com só `.py` é ignorado)

## Limitações conhecidas

- **Conversão é lossy nos extremos**: blocos Notion-only (toggle, callout
  customizado, database, embed) viram markdown padrão no `pull`. Toggles viram
  parágrafo, callouts viram quote.
- **Links relativos `[text](./outro.md)`** viram texto plano (Notion API só
  aceita http/https/mailto/tel). Pra virar link entre páginas Notion seria
  necessário resolver para `mention` — não implementado em v1.
- **Imagens locais** (referências a arquivos no repo) não fazem upload — só
  imagens com URL http(s) são preservadas.
- **`replace-all` no push de READMEs preserva `child_page` blocks**, mas
  reordena: subpáginas aparecem antes do conteúdo do README após re-push.
- **Rate limit do Notion API** (~3 req/s): syncs grandes podem demorar.
- **Headings markdown além de h3** colapsam pra h3 (Notion não tem h4-h6).

## Estrutura de arquivos

```
~/.config/notion-sync/
  └── .env                      # token (chmod 600, fora do git)

<repo>/
  ├── Makefile                  # targets dev:notion-push/pull/status
  ├── .notion-sync.json         # mapping page_id ↔ arquivo (commitado)
  └── scripts/
      ├── notion-sync.py        # script único auto-contido (uv)
      └── README.md             # este arquivo
```

## Estado atual do repo

- Workspace Notion: **Lançamento**
- Página raiz: `Sync / agencia-domapro`
- 42 arquivos `.md` mapeados (36 files + 6 READMEs + 22 pastas)

## Troubleshooting

**`Falha ao acessar página XYZ`**: integration não foi compartilhada com a
página parent. No Notion, abre a página → `...` → Connections → adiciona
"Lançamento".

**`Invalid URL for link`**: tem markdown link com URL não-http/https que o
parser deixou passar. Reporta com o arquivo problemático.

**Sync travou no meio**: state é salvo após cada arquivo, então rodar de novo
retoma de onde parou (idempotente).

**Páginas órfãs / archive cascade**: se uma operação corrompeu a estrutura, o
caminho mais limpo é nukar a página `docs` no Notion (`curl -X DELETE
.../blocks/<docs_page_id>`), zerar `.notion-sync.json` (manter só
`root_page_id` e `local_root`), e rodar `make dev:notion-push` de novo.

**Quero recomeçar do zero**: apaga `.notion-sync.json` e roda
`make notion-init URL=...` de novo. Páginas antigas no Notion ficam órfãs (não
são deletadas automaticamente).

## Rotação do token

1. Gera novo token na Notion: https://www.notion.so/profile/integrations
2. Substitui em `~/.config/notion-sync/.env`
3. Substitui em `~/.claude.json` no campo `mcpServers.notion.env.NOTION_TOKEN`
4. Reinicia Claude Code (`/exit` e abre)
5. Revoga o token antigo na mesma página de integration
