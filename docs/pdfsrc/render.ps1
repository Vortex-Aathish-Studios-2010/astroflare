param([string]$Name)
$edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$docs = "C:\Users\bassi\dev\astroflare-vortex\docs"
$out = "$docs\$Name.pdf"
if (Test-Path $out) { Remove-Item $out -Force }
$p = Start-Process -FilePath $edge -ArgumentList @("--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=20000", "--print-to-pdf=`"$out`"", "file:///C:/Users/bassi/dev/astroflare-vortex/docs/$Name.html") -PassThru -Wait -WindowStyle Hidden
"$Name exit $($p.ExitCode) exists $(Test-Path $out) size $((Get-Item $out -ErrorAction SilentlyContinue).Length)"
