Here are the PowerShell commands to cleanly kill all UI-related processes and start the backend, frontend, and mock Pricing API fresh.

## Step 1 — Kill everything on ports 3000, 3001, and 8000

```powershell
# Kill any process using ports 3000 (frontend), 3001 (backend), and 8000 (mock Pricing API)
Get-NetTCPConnection -LocalPort 3000,3001,8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Also kill any lingering node.exe and python processes from previous runs
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
```

## Step 2 — Start the backend (Terminal 1)

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer
$env:PYTHONPATH="C:\app\enterprise-software-and-ai-compliance-analyzer\agent-brain\src;C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend\src"
py -3.11 -m ui_api.main
```

Wait until you see `INFO: Uvicorn running on http://0.0.0.0:3001`, then:

## Step 3 — Start the mock Pricing API (Terminal 2)

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\mock-pricing-api
$env:PYTHONPATH="C:\app\enterprise-software-and-ai-compliance-analyzer\mock-pricing-api\src"
py -3.11 -m mock_pricing_api.main
```

Wait until you see `INFO: Uvicorn running on http://127.0.0.1:8000`, then:

## Step 4 — Start the frontend (Terminal 3)

```powershell
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\frontend
npm run dev
```

Wait until you see `✓ Compiled / ready`, then open `http://localhost:3000/config` in your browser.

## Quick one-liner to kill + start both

If you want to do it all from a single PowerShell session (backend in background, frontend in foreground):

```powershell
# Kill everything
Get-NetTCPConnection -LocalPort 3000,3001,8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

# Start backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\app\enterprise-software-and-ai-compliance-analyzer; `$env:PYTHONPATH='C:\app\enterprise-software-and-ai-compliance-analyzer\agent-brain\src;C:\app\enterprise-software-and-ai-compliance-analyzer\ui\backend\src'; py -3.11 -m ui_api.main"

# Start mock Pricing API in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\app\enterprise-software-and-ai-compliance-analyzer\mock-pricing-api; `$env:PYTHONPATH='C:\app\enterprise-software-and-ai-compliance-analyzer\mock-pricing-api\src'; py -3.11 -m mock_pricing_api.main"

# Start frontend in current window
cd C:\app\enterprise-software-and-ai-compliance-analyzer\ui\frontend
npm run dev
```

## Port assignments after the fix

| Service | URL |
|---|---|
| UI Frontend | `http://localhost:3000` |
| UI Backend API | `http://localhost:3001/api/*` |
| Mock Pricing API | `http://localhost:8000` |
| Langfuse (when enabled) | `http://localhost:3100` |

Foundry Local is managed from the Configuration page because it is only relevant when the active model provider is `microsoft-foundry-local`. The Dashboard intentionally does not show a Foundry Local health card.
