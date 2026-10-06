# Script para testar responsividade do site em diferentes resoluções
$url = "https://spontaneous-druid-da4ea5.netlify.app"

Write-Host "Testando responsividade do site CRM Dashboards" -ForegroundColor Green
Write-Host "URL: $url" -ForegroundColor Yellow
Write-Host ""

# Lista de resoluções para testar
$resolutions = @(
    @{Name="Mobile"; Width=375; Height=667; Description="iPhone SE"},
    @{Name="Tablet"; Width=768; Height=1024; Description="iPad"},
    @{Name="Desktop HD"; Width=1366; Height=768; Description="Laptop comum"},
    @{Name="Full HD"; Width=1920; Height=1080; Description="Monitor Full HD"},
    @{Name="2K/QHD"; Width=2560; Height=1440; Description="Monitor 2K"},
    @{Name="4K/UHD"; Width=3840; Height=2160; Description="Monitor 4K"}
)

Write-Host "Resoluções a serem testadas:" -ForegroundColor Cyan
foreach ($res in $resolutions) {
    Write-Host "  - $($res.Name) ($($res.Width)x$($res.Height)) - $($res.Description)"
}

Write-Host ""
Write-Host "Para testar a responsividade:" -ForegroundColor Yellow
Write-Host "1. Abra o site em: $url"
Write-Host "2. Pressione F12 para abrir o DevTools"
Write-Host "3. Clique no ícone de dispositivo móvel (Toggle device toolbar)"
Write-Host "4. Teste cada resolução listada acima"
Write-Host ""
Write-Host "Verifique se:" -ForegroundColor Green
Write-Host "  ✓ O layout se adapta corretamente"
Write-Host "  ✓ O texto permanece legível"
Write-Host "  ✓ Os elementos não quebram ou sobrepõem"
Write-Host "  ✓ A navegação funciona em todas as resoluções"
Write-Host "  ✓ Em 4K, os elementos aproveitam o espaço disponível"

# Abrir o site no navegador padrão
Start-Process $url
