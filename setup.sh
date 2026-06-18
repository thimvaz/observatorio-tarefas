#!/bin/bash

# ═════════════════════════════════════════════════════════════════════════════
# 🚀 setup.sh — Script de Configuração Automática
# ═════════════════════════════════════════════════════════════════════════════

set -e

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  🚀 SETUP AUTOMÁTICO — GitHub Actions + DuckDB + Streamlit            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# 1️⃣  VERIFICAR PYTHON
# ─────────────────────────────────────────────────────────────────────────────
echo "1️⃣  Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale primeiro."
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo "   ✅ $PYTHON_VERSION"

# ─────────────────────────────────────────────────────────────────────────────
# 2️⃣  CRIAR AMBIENTE VIRTUAL
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "2️⃣  Criando ambiente virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✅ Ambiente virtual criado"
else
    echo "   ℹ️  Ambiente virtual já existe"
fi

# Ativar ambiente
source venv/bin/activate
echo "   ✅ Ambiente ativado"

# ─────────────────────────────────────────────────────────────────────────────
# 3️⃣  INSTALAR DEPENDÊNCIAS
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "3️⃣  Instalando dependências..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
echo "   ✅ Dependências instaladas"

# ─────────────────────────────────────────────────────────────────────────────
# 4️⃣  VERIFICAR GCP CREDENTIALS
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "4️⃣  Configuração de Credenciais GCP..."

if [ -f "service-account.json" ]; then
    echo "   ℹ️  Arquivo service-account.json encontrado"
else
    echo "   ⚠️  service-account.json não encontrado!"
    echo "   📝 Procedimento:"
    echo "      1. Vá em: https://console.cloud.google.com/iam-admin/serviceaccounts"
    echo "      2. Crie uma Service Account"
    echo "      3. Crie uma chave JSON"
    echo "      4. Salve como 'service-account.json' neste diretório"
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# 5️⃣  EXECUTAR SINCRONIZAÇÃO INICIAL
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "5️⃣  Sincronização Inicial..."
echo ""

if [ -f "service-account.json" ]; then
    echo "   🔄 Carregando dados do Google Drive..."
    export GCP_SERVICE_ACCOUNT="$(cat service-account.json)"
    python3 data_sync.py
    echo ""
else
    echo "   ⚠️  Pulando sincronização (credentials não encontrado)"
    echo "   💡 Execute manualmente depois:"
    echo "      export GCP_SERVICE_ACCOUNT=\"\$(cat service-account.json)\""
    echo "      python3 data_sync.py"
    echo ""
fi

# ─────────────────────────────────────────────────────────────────────────────
# 6️⃣  RESUMO
# ─────────────────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP CONCLUÍDO!                                                   ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Próximos Passos:"
echo ""
echo "   1. Executar app Streamlit:"
echo "      $ streamlit run app.py"
echo ""
echo "   2. Para sincronizar novamente:"
echo "      $ export GCP_SERVICE_ACCOUNT=\"\$(cat service-account.json)\""
echo "      $ python3 data_sync.py"
echo ""
echo "   3. Para fazer commit no Git:"
echo "      $ git add datos_tarefas.duckdb ultimo_update.json"
echo "      $ git commit -m \"Add banco de dados inicial\""
echo "      $ git push"
echo ""
echo "   4. Verificar GitHub Actions:"
echo "      $ Abra seu repositório no GitHub → Actions"
echo ""
echo "📚 Documentação: GUIA_IMPLEMENTACAO.md"
echo ""
