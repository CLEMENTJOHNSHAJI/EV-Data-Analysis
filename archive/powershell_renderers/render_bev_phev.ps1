Add-Type -AssemblyName System.Drawing

$cities = @("Helsinki", "Tampere", "Oulu")
$bev  = @(31408, 8189, 6857)
$phev = @(27108, 8069, 6180)
$bevShare  = @(53.7, 50.4, 52.6)
$phevShare = @(46.3, 49.6, 47.4)

$colorBev  = [System.Drawing.Color]::FromArgb(37, 99, 235)
$colorPhev = [System.Drawing.Color]::FromArgb(245, 158, 11)

$W = 1000; $H = 600
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::White)

$fTitle = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$fSub   = New-Object System.Drawing.Font("Segoe UI", 9)
$fAxis  = New-Object System.Drawing.Font("Segoe UI", 9)
$fLabel = New-Object System.Drawing.Font("Segoe UI", 10)
$fVal   = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
$fLeg   = New-Object System.Drawing.Font("Segoe UI", 10)
$blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
$grayBrush  = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90, 90, 90))
$gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(230, 230, 230), 1)
$axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150, 150, 150), 1)

$title = "BEV vs PHEV Fleet by City"
$ts = $g.MeasureString($title, $fTitle)
$g.DrawString($title, $fTitle, $blackBrush, ($W - $ts.Width) / 2, 14)

$sub = "Cumulative EV fleet (2010-2025) | Source: Traficom (kanta_010)"
$ss = $g.MeasureString($sub, $fSub)
$g.DrawString($sub, $fSub, $grayBrush, ($W - $ss.Width) / 2, 38)

$plotLeft = 88; $plotRight = 962; $plotTop = 92; $plotBottom = 500
$plotW = $plotRight - $plotLeft
$plotH = $plotBottom - $plotTop
$yMax = 36000.0; $yStep = 5000.0
$n = $cities.Count
$groupW = $plotW / $n
$barW = 52
$gap = 10

for ($v = 0; $v -le $yMax; $v += $yStep) {
  $y = $plotBottom - ($v / $yMax) * $plotH
  $g.DrawLine($gridPen, $plotLeft, $y, $plotRight, $y)
  $lbl = "$([int]$v)"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $plotLeft - $ls.Width - 6, $y - $ls.Height / 2)
}

$g.DrawLine($axisPen, $plotLeft, $plotTop, $plotLeft, $plotBottom)
$g.DrawLine($axisPen, $plotLeft, $plotBottom, $plotRight, $plotBottom)

function Ypix($v) { return $plotBottom - ($v / $yMax) * $plotH }

for ($i = 0; $i -lt $n; $i++) {
  $cx = $plotLeft + $groupW * $i + $groupW / 2
  $xBev  = $cx - $barW - $gap / 2
  $xPhev = $cx + $gap / 2

  $hBev  = ($bev[$i]  / $yMax) * $plotH
  $hPhev = ($phev[$i] / $yMax) * $plotH

  $brushBev  = New-Object System.Drawing.SolidBrush($colorBev)
  $brushPhev = New-Object System.Drawing.SolidBrush($colorPhev)
  $g.FillRectangle($brushBev,  $xBev,  $plotBottom - $hBev,  $barW, $hBev)
  $g.FillRectangle($brushPhev, $xPhev, $plotBottom - $hPhev, $barW, $hPhev)
  $brushBev.Dispose(); $brushPhev.Dispose()

  $lblBev  = "$($bev[$i].ToString('N0'))`n($($bevShare[$i])%)"
  $lblPhev = "$($phev[$i].ToString('N0'))`n($($phevShare[$i])%)"
  $lsB = $g.MeasureString($lblBev, $fVal)
  $lsP = $g.MeasureString($lblPhev, $fVal)
  $g.DrawString($lblBev,  $fVal, $blackBrush, $xBev  + ($barW - $lsB.Width) / 2, $plotBottom - $hBev  - $lsB.Height - 4)
  $g.DrawString($lblPhev, $fVal, $blackBrush, $xPhev + ($barW - $lsP.Width) / 2, $plotBottom - $hPhev - $lsP.Height - 4)

  $cl = $cities[$i]
  $cls = $g.MeasureString($cl, $fLabel)
  $g.DrawString($cl, $fLabel, $blackBrush, $cx - $cls.Width / 2, $plotBottom + 8)
}

$xTitle = "City"
$xs = $g.MeasureString($xTitle, $fLabel)
$g.DrawString($xTitle, $fLabel, $blackBrush, ($plotLeft + $plotRight) / 2 - $xs.Width / 2, $plotBottom + 34)

$state = $g.Save()
$g.TranslateTransform(16, ($plotTop + $plotBottom) / 2)
$g.RotateTransform(-90)
$yTitle = "Number of vehicles"
$yts = $g.MeasureString($yTitle, $fLabel)
$g.DrawString($yTitle, $fLabel, $blackBrush, -$yts.Width / 2, 0)
$g.Restore($state)

$legItems = @(
  @{ Name = "BEV"; Color = $colorBev },
  @{ Name = "PHEV"; Color = $colorPhev }
)
$legW = 0
foreach ($item in $legItems) { $legW += 18 + $g.MeasureString($item.Name, $fLeg).Width + 28 }
$lx = ($W - $legW) / 2
$ly = 64
foreach ($item in $legItems) {
  $lb = New-Object System.Drawing.SolidBrush($item.Color)
  $g.FillRectangle($lb, $lx, $ly + 2, 14, 14)
  $g.DrawString($item.Name, $fLeg, $blackBrush, $lx + 18, $ly)
  $lx += 18 + $g.MeasureString($item.Name, $fLeg).Width + 28
  $lb.Dispose()
}

$out = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\ev_bev_phev_fleet.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Saved $out"
