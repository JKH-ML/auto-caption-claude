$env:PYTHONUTF8 = "1"

$files = if ($args.Count -gt 0) { $args } else { Get-ChildItem -Path . -Filter *.mp3 | Select-Object -ExpandProperty FullName }

if ($files.Count -eq 0) {
    Write-Host "현재 폴더에 mp3 파일이 없습니다."
    exit
}

foreach ($file in $files) {
    if (-not (Test-Path $file)) {
        Write-Host "오류: 파일을 찾을 수 없습니다 → $file"
        continue
    }
    python "$PSScriptRoot\auto_caption.py" $file
}
