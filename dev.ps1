# dev.ps1 - Automated Local QA Startup
Write-Host "--- Casting the Vue-Refactor Spell ---" -ForegroundColor Cyan

# 1. Environment & Security
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\venv\Scripts\Activate.ps1

# 2. Set Mana (Environment Variables)
$env:FLASK_DEBUG="1"
$env:CHITCHAT_SECRET_KEY="dev-secret-for-local-testing"
$env:CHITCHAT_DATABASE_URI="postgresql://neondb_owner:npg_ZEKdV8nIQCG7@ep-weathered-dust-aisoxexk-pooler.c-4.us-east-1.aws.neon.tech/chitchat_app?sslmode=require&channel_binding=require"
$env:CHITCHAT_INVITE_CODE="qatest"

# 3. Ignition
Write-Host "Starting server at http://localhost:5000..." -ForegroundColor Green
python run.py