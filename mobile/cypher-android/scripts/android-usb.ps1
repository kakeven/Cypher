$ErrorActionPreference = 'Stop'

if (-not (Get-Command adb -ErrorAction SilentlyContinue)) {
    throw 'adb não foi encontrado. Instale o Android SDK Platform Tools e adicione-o ao PATH.'
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker não foi encontrado no PATH.'
}

$connectedDevices = @(& adb devices | Select-String '\sdevice$')
if ($connectedDevices.Count -eq 0) {
    throw 'Nenhum aparelho autorizado foi encontrado. Conecte o USB, ative a depuração e aceite a chave exibida no celular.'
}

$repositoryPath = Resolve-Path (Join-Path $PSScriptRoot '..\..\..')
Push-Location $repositoryPath
try {
    & docker compose up -d cypher-android
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }

    & adb reverse tcp:5173 tcp:5174
    $viteReady = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        if (Test-NetConnection -ComputerName '127.0.0.1' -Port 5174 -InformationLevel Quiet) {
            $viteReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $viteReady) {
        $viteDetails = & docker compose logs cypher-android --tail 20
        throw "O Vite Docker não respondeu em http://127.0.0.1:5174. Detalhes: $viteDetails"
    }

    & pnpm --dir mobile/cypher-android exec cap run android --live-reload --host 127.0.0.1 --port 5173
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
