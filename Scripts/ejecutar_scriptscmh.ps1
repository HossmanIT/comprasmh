# Ruta de los scripts Python
$transferScript = "C:\Mondayapp\comprasmh\transfercmh.py"
$syncScript = "C:\Mondayapp\comprasmh\sync_scriptcmh.py"
$logFile = "C:\Logs\comprasmh.log"
$transferOut = "C:\Logs\transfercmh_salida.log"
$transferErr = "C:\Logs\transfercmh_error.log"
$syncOut = "C:\Logs\synccmh_salida.log"
$syncErr = "C:\Logs\synccmh_error.log"

# Ruta completa a python.exe (ajusta si usas entorno virtual)
$pythonPath = "python.exe"

# Funcion para escribir logs
function Write-Log {
    param ([string]$message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $message" | Out-File -FilePath $logFile -Append
    Write-Host "$timestamp - $message"
}

# Iniciar registro
Write-Log "==== Inicio de la ejecucion automatica ===="

# 1. Ejecutar transfercmh.py
try {
    Write-Log "Ejecutando transfercmh.py..."
    $transferProcess = Start-Process -FilePath $pythonPath `
        -ArgumentList $transferScript `
        -RedirectStandardOutput $transferOut `
        -RedirectStandardError $transferErr `
        -Wait -PassThru -NoNewWindow

    if ($transferProcess.ExitCode -eq 0) {
        Write-Log "transfercmh.py se ejecuto correctamente (ExitCode: 0)."
    } else {
        Write-Log "ERROR: transfercmh.py fallo (ExitCode: $($transferProcess.ExitCode))."
        exit 1
    }
} catch {
    Write-Log "ERROR al ejecutar transfercmh.py: $_"
    exit 1
}

# 2. Esperar 60 segundos antes de ejecutar sync_scriptcmh.py
Write-Log "Esperando 60 segundos antes de ejecutar sync_scriptcmh.py..."
Start-Sleep -Seconds 60

# 3. Ejecutar sync_scriptcmh.py
try {
    Write-Log "Ejecutando sync_scriptcmh.py..."
    $syncProcess = Start-Process -FilePath $pythonPath `
        -ArgumentList $syncScript `
        -RedirectStandardOutput $syncOut `
        -RedirectStandardError $syncErr `
        -Wait -PassThru -NoNewWindow

    if ($syncProcess.ExitCode -eq 0) {
        Write-Log "sync_scriptcmh.py se ejecuto correctamente (ExitCode: 0)."
    } else {
        Write-Log "ERROR: sync_scriptcmh.py fallo (ExitCode: $($syncProcess.ExitCode))."
        exit 1
    }
} catch {
    Write-Log "ERROR al ejecutar sync_scriptcmh.py: $_"
    exit 1
}

Write-Log "==== Ejecucion completada ===="
