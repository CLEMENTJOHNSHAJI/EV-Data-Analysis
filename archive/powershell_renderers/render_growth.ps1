Add-Type -AssemblyName System.Drawing

# Data: annual growth rate (%) of cumulative EV fleet, 2013-2025
$years = 2013,2014,2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025
$series = [ordered]@{
  "Helsinki" = @(248.1,100.0,113.8,93.0,80.2,56.8,47.8,72.9,65.0,40.6,41.0,23.0,20.2)
  "Tampere"  = @(217.9,68.5,104.3,79.4,65.7,51.1,41.6,69.0,54.6,33.3,25.4,14.2,12.8)
  "Oulu"     = @(210.0,73.1,88.2,85.1,72.5,52.1,50.7,72.3,53.5,32.2,24.4,14.0,12.6)
}
$colors = @{
  "Helsinki" = [System.Drawing.Color]::FromArgb(37,99,235)
  "Tampere"  = [System.Drawing.Color]::FromArgb(239,68,68)
  "Oulu"     = [System.Drawing.Color]::FromArgb(16,185,129)
}

$W = 1000; $H = 560
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::White)

$fTitle = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fAxis  = New-Object System.Drawing.Font("Segoe UI", 9)
$fLabel = New-Object System.Drawing.Font("Segoe UI", 10)
$fLeg   = New-Object System.Drawing.Font("Segoe UI", 10)
$blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26,26,26))
$grayBrush  = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90,90,90))
$gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(230,230,230), 1)
$axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150,150,150), 1)

# Title
$title = "Annual Growth Rate of Cumulative EV Fleet (2013-2025)"
$ts = $g.MeasureString($title, $fTitle)
$g.DrawString($title, $fTitle, $blackBrush, ($W - $ts.Width)/2, 14)

# Plot geometry
$plotLeft = 88; $plotRight = 962; $plotTop = 78; $plotBottom = 495
$plotW = $plotRight - $plotLeft
$plotH = $plotBottom - $plotTop
$yMax = 280.0; $yStep = 40.0
$n = $years.Count

# Y gridlines + labels
for ($v = 0; $v -le $yMax; $v += $yStep) {
  $y = $plotBottom - ($v / $yMax) * $plotH
  $g.DrawLine($gridPen, $plotLeft, $y, $plotRight, $y)
  $lbl = "$([int]$v) %"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $plotLeft - $ls.Width - 6, $y - $ls.Height/2)
}
# Axes
$g.DrawLine($axisPen, $plotLeft, $plotTop, $plotLeft, $plotBottom)
$g.DrawLine($axisPen, $plotLeft, $plotBottom, $plotRight, $plotBottom)

# X labels
for ($i = 0; $i -lt $n; $i++) {
  $x = $plotLeft + $plotW * $i / ($n - 1)
  $lbl = "$($years[$i])"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width/2, $plotBottom + 6)
}

# Axis titles
$xTitle = "Year"
$xs = $g.MeasureString($xTitle, $fLabel)
$g.DrawString($xTitle, $fLabel, $blackBrush, ($plotLeft + $plotRight)/2 - $xs.Width/2, $plotBottom + 28)
$state = $g.Save()
$g.TranslateTransform(16, ($plotTop + $plotBottom)/2)
$g.RotateTransform(-90)
$yTitle = "Annual growth rate (%)"
$yts = $g.MeasureString($yTitle, $fLabel)
$g.DrawString($yTitle, $fLabel, $blackBrush, -$yts.Width/2, 0)
$g.Restore($state)

# Series lines + points
function Ypix($v) { return $plotBottom - ($v / $yMax) * $plotH }
foreach ($city in $series.Keys) {
  $data = $series[$city]
  $pen = New-Object System.Drawing.Pen($colors[$city], 2.5)
  $brush = New-Object System.Drawing.SolidBrush($colors[$city])
  for ($i = 0; $i -lt $n - 1; $i++) {
    $x1 = $plotLeft + $plotW * $i / ($n - 1)
    $x2 = $plotLeft + $plotW * ($i + 1) / ($n - 1)
    $g.DrawLine($pen, $x1, (Ypix $data[$i]), $x2, (Ypix $data[$i+1]))
  }
  for ($i = 0; $i -lt $n; $i++) {
    $x = $plotLeft + $plotW * $i / ($n - 1)
    $y = Ypix $data[$i]
    $g.FillEllipse($brush, $x - 3.5, $y - 3.5, 7, 7)
  }
  $pen.Dispose(); $brush.Dispose()
}

# Legend (top, centered)
$legItems = @($series.Keys)
$legW = 0
foreach ($c in $legItems) { $legW += 28 + $g.MeasureString($c, $fLeg).Width + 22 }
$lx = ($W - $legW)/2
$ly = 48
foreach ($c in $legItems) {
  $lb = New-Object System.Drawing.SolidBrush($colors[$c])
  $lp = New-Object System.Drawing.Pen($colors[$c], 2.5)
  $g.DrawLine($lp, $lx, $ly + 8, $lx + 22, $ly + 8)
  $g.FillEllipse($lb, $lx + 8, $ly + 4.5, 7, 7)
  $g.DrawString($c, $fLeg, $blackBrush, $lx + 28, $ly)
  $lx += 28 + $g.MeasureString($c, $fLeg).Width + 22
  $lb.Dispose(); $lp.Dispose()
}

$out = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\ev_fleet_growth_rate.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Saved $out"
