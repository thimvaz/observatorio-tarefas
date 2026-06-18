# 🚀 Guia de Implementação: GitHub Actions + DuckDB

## 📋 Resumo da Mudança

**Antes:** App carregava dados diretamente do Google Drive a cada execução ❌ Lento  
**Depois:** GitHub Actions sincroniza dados para DuckDB 3x/dia → App lê do DuckDB ✅ Rápido

---

## 🎯 Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `.github/workflows/sync_dados.yml` | Workflow do GitHub Actions (agendador) |
| `data_sync.py` | Script de sincronização Drive → DuckDB |
| `duckdb_loader.py` | Carregador de dados do DuckDB |
| `app.py` | App modificado (use como substituto) |
| `requirements.txt` | Dependências atualizadas |
| `.gitignore` | Configuração Git |

---

## 🔧 PASSO-A-PASSO DE IMPLEMENTAÇÃO

### **PASSO 1: Preparar o Repositório Git**

Se você ainda não tiver um repositório Git, crie um:

```bash
cd seu-projeto
git init
git add .
git commit -m "Inicial"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/SEU_REPO.git
git push -u origin main
```

---

### **PASSO 2: Configurar GitHub Secrets**

⚠️ **IMPORTANTE:** As credenciais da GCP NÃO devem ir para o repositório!

1. Vá até seu repositório no GitHub
2. Clique em **Settings** → **Secrets and variables** → **Actions**
3. Clique em **New repository secret**
4. Crie um secret chamado `GCP_SERVICE_ACCOUNT`
5. **Cole o conteúdo completo** do seu arquivo `service-account.json` como valor

Exemplo do conteúdo:
```json
{
  "type": "service_account",
  "project_id": "seu-projeto",
  "private_key_id": "...",
  "private_key": "...",
  ...
}
```

---

### **PASSO 3: Adicionar o Workflow ao Repositório**

```bash
# Criar o diretório
mkdir -p .github/workflows

# Copiar o arquivo
cp sync_dados.yml .github/workflows/

# Fazer commit
git add .github/workflows/sync_dados.yml
git commit -m "Add GitHub Actions workflow para sincronizar dados"
git push
```

---

### **PASSO 4: Atualizar Requirements**

```bash
# Substituir requirements.txt
cp requirements.txt requirements.txt.backup
# (Use o requirements.txt fornecido)

git add requirements.txt
git commit -m "Add duckdb e atualizar dependências"
git push
```

---

### **PASSO 5: Adicionar Novos Arquivos**

```bash
# Copiar os arquivos de sincronização
cp data_sync.py seu-projeto/
cp duckdb_loader.py seu-projeto/

# Copiar app modificado
cp app_modificado.py seu-projeto/app.py

# Fazer commit
git add data_sync.py duckdb_loader.py app.py
git commit -m "Implementar sincronização com DuckDB"
git push
```

---

### **PASSO 6: Executar Sincronização Inicial (IMPORTANTE!)**

Execute localmente ANTES de confiar no GitHub Actions:

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar sincronização
export GCP_SERVICE_ACCOUNT="$(cat /caminho/para/service-account.json)"
python data_sync.py
```

Você deverá ver:
```
======================================================================
🔄 SINCRONIZANDO DADOS — Google Drive → DuckDB
======================================================================
🔗 Conectando ao Google Drive...
📄 Encontrados 5 arquivo(s)
  ⬇️  [1/5] Baixando: Física - 1º Ano - Módulo 1 - dose mínima
    ✅ Física - 1º Ano - Módulo 1 - dose mínima.xlsx processado (45 linhas)
...
✅ Total: 1250 registros carregados

📊 Salvando em DuckDB: dados_tarefas.duckdb
⏰ Última atualização: 2024-01-15T14:30:00
✅ Dados salvos com sucesso!

======================================================================
✅ SINCRONIZAÇÃO CONCLUÍDA em 2024-01-15T14:30:00
======================================================================
```

Se tudo correr bem, você terá:
- `dados_tarefas.duckdb` (banco de dados)
- `ultimo_update.json` (metadados)

---

### **PASSO 7: Testar o App Localmente**

```bash
streamlit run app.py
```

Você deverá ver:
- 🕐 Última atualização: 15/01/2024 às 14:30
- Dados carregando MUITO mais rápido ⚡

---

### **PASSO 8: Fazer Commit e Push**

```bash
git add dados_tarefas.duckdb ultimo_update.json
git commit -m "Add banco de dados inicial DuckDB"
git push
```

---

## ⏰ AGENDAMENTO DO GITHUB ACTIONS

O workflow está configurado para rodar:

- **9h da manhã** (horário de Brasília)
- **11h da manhã** (horário de Brasília)
- **15h da tarde** (horário de Brasília)
- **Segunda a sexta**

### Verificar Execução

1. Vá até seu repositório no GitHub
2. Clique em **Actions**
3. Procure por "Sincronizar Dados do Google Drive → DuckDB"
4. Clique para ver logs

Se falhar, verifique:
- ✅ O secret `GCP_SERVICE_ACCOUNT` está correto?
- ✅ A pasta do Drive ID está correta em `data_sync.py`?
- ✅ Os arquivos xlsx têm o formato esperado?

---

## 🧪 TESTES MANUAIS

Você pode disparar manualmente o workflow:

1. GitHub → Actions
2. "Sincronizar Dados" → **Run workflow**
3. Selecionar branch `main`
4. Clicar em **Run workflow**

---

## 📊 ESTRUTURA DO BANCO DUCKDB

A tabela `tarefas` tem as seguintes colunas:

```
nome               VARCHAR     (nome do aluno)
Matrícula          VARCHAR     (RM)
Turma              VARCHAR     (ex: "1º A")
serie              VARCHAR     (ex: "1º Ano")
materia            VARCHAR     (ex: "Física")
tipo               VARCHAR     (dose mínima, dose para leão, Padrão)
etapa_nome         VARCHAR     (ex: "Módulo 1")
etapa_num          INTEGER     (número do módulo)
percentual_realizado FLOAT     (0-100)
```

---

## 🚨 TROUBLESHOOTING

### ❌ "DuckDB not found"
```bash
# Execute localmente primeiro
python data_sync.py
```

### ❌ "GCP_SERVICE_ACCOUNT not found"
Verifique se você configurou o secret no GitHub corretamente (Settings → Secrets)

### ❌ Dados desatualizados
Espere até a próxima sincronização automática (9h, 11h ou 15h)  
OU execute manualmente via GitHub Actions

### ❌ Arquivo xlsx com formato diferente
Edite `data_sync.py` linha 70-85 para ajustar parsing

---

## 💡 OTIMIZAÇÕES FUTURAS

1. **Sincronização incremental:** apenas atualizar registros novos/modificados
2. **Backup automático:** salvar versões anteriores do banco
3. **Notificações:** enviar email se sincronização falhar
4. **Cache em S3/GCS:** caso o DuckDB fique muito grande

---

## 📞 DÚVIDAS?

- **GitHub Actions não dispara?** Verifique a aba "Actions" do repositório
- **Dados antigos?** Aguarde sincronização de 15h, ou execute manualmente
- **Quer mudar horários?** Edite `.github/workflows/sync_dados.yml` (valores `cron`)

---

**Autor:** Vaz  
**Data:** Janeiro 2025  
**Status:** ✅ Pronto para produção
