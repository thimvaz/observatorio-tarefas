# Painel de Tarefas — Setup

## Estrutura do projeto

```
painel_tarefas/
├── app.py                          # Aplicação Streamlit principal
├── data_loader.py                  # Leitura dos arquivos do Google Drive
├── requirements.txt
├── .gitignore
└── .streamlit/
    ├── secrets.toml                # ⚠️ NÃO suba ao GitHub (já no .gitignore)
    └── secrets.toml.template       # Modelo para preencher
```

---

## 1. Credenciais (local)

Copie o template e preencha com os dados da service account:

```bash
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# edite .streamlit/secrets.toml com os valores reais
```

---

## 2. Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 3. Deploy no Streamlit Cloud

1. Suba o projeto para um repositório **privado** no GitHub (sem o secrets.toml)
2. Acesse https://share.streamlit.io → "New app" → aponte para o repositório
3. Em **Settings → Secrets**, cole o conteúdo do seu secrets.toml

---

## 4. Pasta do Drive

- ID da pasta configurado em `data_loader.py`: `FOLDER_ID`
- A secretaria deve salvar os arquivos nessa pasta
- O app recarrega os dados a cada 5 minutos (cache `ttl=300`)
- Para forçar atualização: botão **⟳** no canto superior direito do Streamlit

---

## 5. Convenção dos arquivos

Cada arquivo exportado do Plurall deve ter a **célula A1** no formato:

```
Matemática - 7s - módulo 8 - dose mínima
```

Partes separadas por ` - ` (espaço-traço-espaço):
1. Matéria
2. Série (ex: `7s`, `9s`)
3. Módulo (ex: `módulo 8`)
4. Tipo (`dose mínima` ou `dose para leão`)

Arquivos com A1 fora desse padrão são ignorados com aviso.

---

## 6. Configurações ajustáveis (em app.py)

| Variável | Padrão | Descrição |
|---|---|---|
| `PERCENTUAL_MINIMO` | `50` | Abaixo disso → tarefa "não feita" |
| `MIN_TAREFAS_ALERTA` | `3` | Nº de tarefas pendentes para gerar alerta |
