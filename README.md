# SITREP // Oriente Médio — Dashboard Automático

Dashboard de inteligência que atualiza automaticamente a cada 6h via **GitHub Actions + GitHub Pages**. Nenhum servidor necessário.

## Estrutura do projeto

```
.
├── .github/
│   └── workflows/
│       ├── sitrep.yml      ← roda fetch_sitrep.py a cada 6h e commita o JSON
│       └── deploy.yml      ← deploya a pasta public/ no GitHub Pages
├── public/
│   ├── index.html          ← dashboard estático (lê data.json)
│   └── data.json           ← gerado automaticamente pelo fetcher
└── fetch_sitrep.py         ← script Python que chama a API do Claude
```

## Setup (5 minutos)

### 1. Crie o repositório

```bash
# Clone ou crie um novo repo no GitHub
git init sitrep && cd sitrep
# copie os arquivos do projeto aqui
git add . && git commit -m "init"
git remote add origin https://github.com/SEU_USUARIO/sitrep.git
git push -u origin main
```

### 2. Adicione o segredo da API

No repositório do GitHub:
1. Vá em **Settings → Secrets and variables → Actions**
2. Clique em **New repository secret**
3. Nome: `ANTHROPIC_API_KEY`
4. Valor: sua chave da API da Anthropic (`sk-ant-...`)

### 3. Ative o GitHub Pages

1. Vá em **Settings → Pages**
2. Em "Source", selecione **GitHub Actions**
3. Salve

### 4. Primeiro deploy

Vá em **Actions → Deploy GitHub Pages → Run workflow** para fazer o primeiro deploy manual.

Em seguida, vá em **Actions → SITREP — Atualizar Dados → Run workflow** para buscar os dados pela primeira vez.

Após alguns minutos, o site estará disponível em:
```
https://SEU_USUARIO.github.io/sitrep/
```

## Agendamento

O fetcher roda automaticamente em:

| UTC   | BRT   |
|-------|-------|
| 00:00 | 21:00 |
| 06:00 | 03:00 |
| 12:00 | 09:00 |
| 18:00 | 15:00 |

Você também pode disparar manualmente pela aba **Actions** do GitHub.

## Como funciona

```
GitHub Actions (cron 6h)
    └─ fetch_sitrep.py
          ├─ chama Claude API (4x, uma por seção)
          │    └─ Claude usa web_search para buscar dados frescos
          ├─ salva public/data.json
          └─ git commit + push → dispara deploy.yml
                └─ GitHub Pages serve index.html + data.json
```

## Custo estimado

- GitHub Actions: gratuito (2.000 min/mês no plano free; cada run usa ~5 min)
- GitHub Pages: gratuito
- API Anthropic: ~4 chamadas × 4x/dia × 30 dias = ~480 chamadas/mês
  (custo estimado: < $2/mês com Claude Sonnet)
