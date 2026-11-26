$port = 8137
$root = "C:\Users\jshaji\Documents\Thesis\EV_Data_code"
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
$listener.Start()
Write-Host "Serving $root on http://localhost:$port/"
while ($listener.IsListening) {
    $context = $listener.GetContext()
    $rel = $context.Request.Url.LocalPath.TrimStart('/')
    if ([string]::IsNullOrEmpty($rel)) { $rel = "charger_chart.html" }
    $path = Join-Path $root $rel
    if (Test-Path $path) {
        $bytes = [System.IO.File]::ReadAllBytes($path)
        if ($path -match '\.html$') { $context.Response.ContentType = "text/html" }
        $context.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    } else {
        $context.Response.StatusCode = 404
    }
    $context.Response.Close()
}
