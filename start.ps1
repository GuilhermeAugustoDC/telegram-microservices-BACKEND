# Script PowerShell para iniciar o backend do Telegram MicroSaaS
# Executa o servidor FastAPI com uvicorn

Write-Host "🚀 Iniciando Backend do Telegram MicroSaaS..." -ForegroundColor Green
Write-Host "📍 Diretório: $(Get-Location)" -ForegroundColor Yellow

# Verifica se o ambiente virtual existe
if (Test-Path "venv\Scripts\activate.ps1") {
    Write-Host "✅ Ativando ambiente virtual..." -ForegroundColor Cyan
    & "venv\Scripts\activate.ps1"
}
else {
    Write-Host "⚠️  Ambiente virtual não encontrado. Certifique-se de que está na pasta backend." -ForegroundColor Red
    Write-Host "💡 Execute: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Verifica se as dependências estão instaladas
Write-Host "📦 Verificando dependências..." -ForegroundColor Cyan
if (!(Test-Path "requirements.txt")) {
    Write-Host "❌ Arquivo requirements.txt não encontrado!" -ForegroundColor Red
    exit 1
}

# Inicia o servidor
Write-Host "🌐 Iniciando servidor FastAPI..." -ForegroundColor Green
Write-Host "📡 Backend rodará em: http://localhost:8000" -ForegroundColor Magenta
Write-Host "📋 API Docs em: http://localhost:8000/docs" -ForegroundColor Magenta
Write-Host "" 
Write-Host "⏹️  Para parar o servidor, pressione Ctrl+C" -ForegroundColor Yellow

try {
    python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
}
catch {
    Write-Host "❌ Erro ao iniciar o servidor: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Certifique-se de que as dependências estão instaladas: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
