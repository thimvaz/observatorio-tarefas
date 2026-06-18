# ❓ FAQ — Perguntas Frequentes

## 🎯 Geral

### P: Por que usar DuckDB em vez de banco de dados tradicional?
**R:** DuckDB é perfeito para este caso porque:
- ⚡ Muito rápido (OLAP otimizado)
- 📦 Sem servidor — tudo em um arquivo
- 🔓 Open source
- 🐍 Integra perfeitamente com pandas
- 💰 Gratuito

### P: E se os dados ficarem muito grandes?
**R:** Possibilidades:
1. Manter no DuckDB (suporta GB sem problema)
2. Migrar para PostgreSQL/MySQL
3. Usar DuckDB + S3 (MotherDuck)
4. Compressão: DuckDB comprime automaticamente

### P: Posso usar isso sem GitHub?
**R:** Sim! Você pode:
1. Executar `python data_sync.py` em um agendador local (cron, Task Scheduler)
2. Colocar em um VPS com script cron
3. Usar GitHub Actions (recomendado — é gratuito)

---

## 🔧 Configuração

### P: Onde acho o ID da pasta do Google Drive?
**R:** 
1. Abra a pasta no Google Drive
2. A URL é: `https://drive.google.com/drive/folders/AQUI_ESTA_O_ID`
3. Copie tudo depois de `/folders/`

### P: Como criar um service account no GCP?
**R:**
1. Vá em https://console.cloud.google.com/iam-admin/serviceaccounts
2. Crie um novo projeto (se não tiver)
3. Clique em **Create Service Account**
4. Preencha nome: "Sincronizador de Tarefas"
5. Clique em **Create and Continue**
6. Na aba "Keys", crie uma chave JSON
7. Salve como `service-account.json`

### P: Como compartilhar a pasta do Drive com a service account?
**R:**
1. Abra `service-account.json`
2. Copie o email em `client_email`
3. Compartilhe a pasta do Drive com esse email
4. Não precisa aceitar convite (é conta de serviço)

### P: Como mudo os horários de sincronização?
**R:** Edite `.github/workflows/sync_dados.yml`:
```yaml
schedule:
  - cron: '0 14 * * 1-5'  # 9h (Brasília)
  - cron: '0 16 * * 1-5'  # 11h
  - cron: '0 20 * * 1-5'  # 15h
```

Usar https://crontab.guru para converter horários.

---

## ⚡ Performance

### P: Por que o app ficou tão mais rápido?
**R:** Porque:
- ❌ Antes: Baixar 5-10 arquivos do Drive toda vez (2-3s)
- ✅ Depois: Ler arquivo local (50-100ms)

### P: Posso usar cache do Streamlit?
**R:** Sim! Já está no código (`@st.cache_data`).

---

## 🚨 Troubleshooting

### P: "DuckDB file not found"
**R:** Você não executou `python data_sync.py` ainda.
```bash
export GCP_SERVICE_ACCOUNT="$(cat service-account.json)"
python3 data_sync.py
```

### P: Workflow falha com erro de autenticação
**R:** O secret `GCP_SERVICE_ACCOUNT` está incorreto.
1. Vá em GitHub → Settings → Secrets
2. Delete `GCP_SERVICE_ACCOUNT`
3. Recrie com o conteúdo correto de `service-account.json`

### P: Dados aparecem desatualizados
**R:**
- Verificar se sincronização rodou: GitHub → Actions
- Se falhou, clicar em **Run workflow** manualmente
- Ou esperar próximo horário agendado (9h, 11h ou 15h)

### P: A importação de `duckdb_loader` falha
**R:** Você trocou os arquivos certo?
```bash
# Verificar arquivos existem
ls app.py duckdb_loader.py data_sync.py
```

### P: Erro "Coluna de percentual não encontrada"
**R:** Formato dos arquivos xlsx mudou.
1. Editar `data_sync.py` linhas 75-85
2. Ajustar lógica de parsing
3. Executar `python data_sync.py` novamente

---

## 📊 Consultas ao DuckDB

### P: Como posso consultar os dados diretamente?
**R:**
```python
import duckdb

conn = duckdb.connect('dados_tarefas.duckdb')
df = conn.execute("""
    SELECT nome, materia, percentual_realizado 
    FROM tarefas 
    WHERE percentual_realizado < 50
""").fetchdf()
print(df)
```

### P: Como exportar dados para CSV?
**R:**
```python
import duckdb

conn = duckdb.connect('dados_tarefas.duckdb')
conn.execute("""
    COPY (SELECT * FROM tarefas) 
    TO 'export.csv' (FORMAT CSV, HEADER TRUE)
""")
```

---

## 🔐 Segurança

### P: Devo fazer commit do DuckDB?
**R:** 
- ✅ SIM — com Git LFS (Large File Storage) para rastrear mudanças
- ✅ SIM — commit normal (arquivo pequeno geralmente)
- ⚠️ NÃO commit — se usar `.gitignore` (terá de sincronizar manualmente)

### P: E se compartilhar o repositório público?
**R:**
- ✅ Service account JSON NÃO será visível (está em GitHub Secrets)
- ✅ DuckDB será visível, mas sem dados sensíveis
- ✅ Outras pessoas podem ler dados de tarefas (mas sem senha)

---

## 🧪 Desenvolvimento

### P: Como adicionar teste local antes de commitar?
**R:**
```bash
# Testar sincronização
export GCP_SERVICE_ACCOUNT="$(cat service-account.json)"
python3 data_sync.py

# Testar app
streamlit run app.py

# Depois commit
git add .
git commit -m "..."
git push
```

### P: Como debugar se algo der errado?
**R:**
1. Abrir `data_sync.py`
2. Adicionar `print()` onde necessário
3. Executar localmente: `python data_sync.py`
4. Ver logs detalhados
5. Depois usar GitHub Actions com confiança

---

## 📞 Mais Ajuda

- **GitHub Actions docs:** https://docs.github.com/en/actions
- **DuckDB docs:** https://duckdb.org/docs/
- **Streamlit docs:** https://docs.streamlit.io/

---

**Atualizado:** Janeiro 2025  
**Mantido por:** Vaz
