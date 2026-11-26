Add-Type -AssemblyName System.Drawing

# Ordered by CARI rank (highest first)
$cities = @("Tampere", "Helsinki", "Oulu")
$ranks  = @(1, 2, 3)
$cari   = @(0.0965, 0.0646, 0.0576)
$ics    = @(2040, 4765, 1089)
$fleet  = @(16258, 58516, 13037)
$cf     = @(1.30, 1.26, 1.45)

$colorCari = @(
  [System.Drawing.Color]::FromArgb(22, 163, 74),
  [System.Drawing.Color]::FromArgb(249, 115, 22),
  [System.Drawing.Color]::FromArgb(220, 38, 38)
)

function Render-CariChart($path) {
  $W = 1000; $H = 460
  $bmp = New-Object System.Drawing.Bitmap($W, $H)
  $g = [System.Drawing.Graphics]::FromImage($bmp)
  $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
  $g.Clear([System.Drawing.Color]::White)

  $fTitle = New-Object System.Drawing.Font("Segoe UI", 15, [System.Drawing.FontStyle]::Bold)
  $fSub   = New-Object System.Drawing.Font("Segoe UI", 9)
  $fAxis  = New-Object System.Drawing.Font("Segoe UI", 9)
  $fLabel = New-Object System.Drawing.Font("Segoe UI", 10)
  $fVal   = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
  $fNote  = New-Object System.Drawing.Font("Segoe UI", 8.5)
  $blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
  $grayBrush  = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90, 90, 90))
  $gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(230, 230, 230), 1)
  $axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150, 150, 150), 1)

  $title = "Climate-Adjusted Readiness Index (CARI)"
  $ts = $g.MeasureString($title, $fTitle)
  $g.DrawString($title, $fTitle, $blackBrush, ($W - $ts.Width) / 2, 14)

  $sub = "CARI = ICS / (Total EV Fleet x Climate Factor)   |   Higher value = stronger climate-adjusted charging readiness"
  $ss = $g.MeasureString($sub, $fSub)
  $g.DrawString($sub, $fSub, $grayBrush, ($W - $ss.Width) / 2, 40)

  $n = $cities.Count
  $plotLeft = 210; $plotRight = 940; $plotTop = 82; $plotBottom = 380
  $plotW = $plotRight - $plotLeft
  $plotH = $plotBottom - $plotTop
  $xMax = 0.11
  $barH = 46
  $groupH = $plotH / $n

  for ($v = 0; $v -le $xMax; $v += 0.02) {
    $x = $plotLeft + ($v / $xMax) * $plotW
    $g.DrawLine($gridPen, $x, $plotTop, $x, $plotBottom)
    $lbl = "$([math]::Round($v, 2))"
    $ls = $g.MeasureString($lbl, $fAxis)
    $g.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $plotBottom + 6)
  }
  $g.DrawLine($axisPen, $plotLeft, $plotTop, $plotLeft, $plotBottom)
  $g.DrawLine($axisPen, $plotLeft, $plotBottom, $plotRight, $plotBottom)

  for ($i = 0; $i -lt $n; $i++) {
    $cy = $plotTop + $groupH * $i + $groupH / 2
    $y = $cy - $barH / 2
    $w = ($cari[$i] / $xMax) * $plotW
    $brush = New-Object System.Drawing.SolidBrush($colorCari[$i])
    $g.FillRectangle($brush, $plotLeft, $y, $w, $barH)
    $brush.Dispose()

    $ylabel = "#$($ranks[$i])  $($cities[$i])"
    $yls = $g.MeasureString($ylabel, $fLabel)
    $g.DrawString($ylabel, $fLabel, $blackBrush, $plotLeft - $yls.Width - 14, $cy - $yls.Height / 2)

    $calc = "$($ics[$i].ToString('N0')) / ($($fleet[$i].ToString('N0')) x $($cf[$i])) = $($cari[$i])"
    $flbl = "$($cari[$i])"
    $fls = $g.MeasureString($flbl, $fVal)
    $g.DrawString($flbl, $fVal, $blackBrush, $plotLeft + $w + 8, $cy - $fls.Height / 2)
    $g.DrawString($calc, $fNote, $grayBrush, $plotLeft + $w + 8, $cy + $fls.Height / 2 + 1)
  }

  $xTitle = "Climate-Adjusted Readiness Index (CARI)"
  $xts = $g.MeasureString($xTitle, $fLabel)
  $g.DrawString($xTitle, $fLabel, $blackBrush, ($plotLeft + $plotRight) / 2 - $xts.Width / 2, $plotBottom + 30)

  $bmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $g.Dispose(); $bmp.Dispose()
  Write-Host "Saved $path"
}

Render-CariChart "C:\Users\jshaji\Documents\Thesis\EV_Data_code\cari.png"
Render-CariChart "C:\Users\jshaji\Documents\Thesis\EV_Data_code\cari_ranking.png"
