Add-Type -AssemblyName System.Drawing

$cities = @("Helsinki", "Tampere", "Oulu")
$type2w = @(2690, 975, 377)
$chadw  = @(120, 30, 42)
$ccsw   = @(1955, 1035, 670)
$ics    = @(4765, 2040, 1089)
$evFleet = @(58516, 16258, 13037)
$ratio  = @(12.28, 7.97, 11.97)

$colorType2 = [System.Drawing.Color]::FromArgb(37, 99, 235)
$colorCha   = [System.Drawing.Color]::FromArgb(245, 158, 11)
$colorCcs   = [System.Drawing.Color]::FromArgb(16, 185, 129)
$colorRatio = @(
  [System.Drawing.Color]::FromArgb(220, 38, 38),
  [System.Drawing.Color]::FromArgb(22, 163, 74),
  [System.Drawing.Color]::FromArgb(234, 88, 12)
)

$W = 1100; $H = 700
$bmp = New-Object System.Drawing.Bitmap($W, $H)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
$g.Clear([System.Drawing.Color]::White)

$fTitle = New-Object System.Drawing.Font("Segoe UI", 15, [System.Drawing.FontStyle]::Bold)
$fSub   = New-Object System.Drawing.Font("Segoe UI", 9)
$fPanel = New-Object System.Drawing.Font("Segoe UI", 11, [System.Drawing.FontStyle]::Bold)
$fAxis  = New-Object System.Drawing.Font("Segoe UI", 9)
$fLabel = New-Object System.Drawing.Font("Segoe UI", 10)
$fVal   = New-Object System.Drawing.Font("Segoe UI", 8.5, [System.Drawing.FontStyle]::Bold)
$fLeg   = New-Object System.Drawing.Font("Segoe UI", 9.5)
$fNote  = New-Object System.Drawing.Font("Segoe UI", 8.5)
$blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
$grayBrush  = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90, 90, 90))
$gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(230, 230, 230), 1)
$axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150, 150, 150), 1)

$title = "EVs per Infrastructure Capacity Unit"
$ts = $g.MeasureString($title, $fTitle)
$g.DrawString($title, $fTitle, $blackBrush, ($W - $ts.Width) / 2, 14)

$sub = "ICS = Type 2 + (3 x CHAdeMO) + (5 x CCS)   |   EVs per Capacity Unit = Total EV Fleet / ICS   |   Lower = better infrastructure availability"
$ss = $g.MeasureString($sub, $fSub)
$g.DrawString($sub, $fSub, $grayBrush, ($W - $ss.Width) / 2, 40)

function DrawPanelTitle($text, $y) {
  $size = $g.MeasureString($text, $fPanel)
  $g.DrawString($text, $fPanel, $blackBrush, ($W - $size.Width) / 2, $y)
}

function Ypix($v, $plotBottom, $plotH, $yMax) {
  return $plotBottom - ($v / $yMax) * $plotH
}

# Legend (centered below subtitle, above panel A)
$legA = @(
  @{ Name = "Type 2 (x1)"; Color = $colorType2 },
  @{ Name = "CHAdeMO (x3)"; Color = $colorCha },
  @{ Name = "CCS Fast (x5)"; Color = $colorCcs }
)
$legW = 0
foreach ($item in $legA) { $legW += 18 + $g.MeasureString($item.Name, $fLeg).Width + 24 }
$lx = ($W - $legW) / 2
$ly = 62
foreach ($item in $legA) {
  $lb = New-Object System.Drawing.SolidBrush($item.Color)
  $g.FillRectangle($lb, $lx, $ly + 2, 14, 14)
  $g.DrawString($item.Name, $fLeg, $blackBrush, $lx + 18, $ly)
  $lx += 18 + $g.MeasureString($item.Name, $fLeg).Width + 24
  $lb.Dispose()
}

# Panel A: stacked ICS composition
DrawPanelTitle "A. Weighted Infrastructure Capacity Score (ICS) by City" 96
$plotLeft = 90; $plotRight = 1040; $plotTop = 126; $plotBottom = 360
$plotW = $plotRight - $plotLeft
$plotH = $plotBottom - $plotTop
$yMaxA = 5200.0; $yStepA = 1000.0
$n = $cities.Count
$groupW = $plotW / $n
$barW = 90

for ($v = 0; $v -le $yMaxA; $v += $yStepA) {
  $y = Ypix $v $plotBottom $plotH $yMaxA
  $g.DrawLine($gridPen, $plotLeft, $y, $plotRight, $y)
  $lbl = "$([int]$v)"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $plotLeft - $ls.Width - 6, $y - $ls.Height / 2)
}
$g.DrawLine($axisPen, $plotLeft, $plotTop, $plotLeft, $plotBottom)
$g.DrawLine($axisPen, $plotLeft, $plotBottom, $plotRight, $plotBottom)

for ($i = 0; $i -lt $n; $i++) {
  $cx = $plotLeft + $groupW * $i + $groupW / 2
  $x = $cx - $barW / 2
  $segments = @(
    @{ Val = $type2w[$i]; Color = $colorType2 },
    @{ Val = $chadw[$i];  Color = $colorCha },
    @{ Val = $ccsw[$i];   Color = $colorCcs }
  )
  $stackTop = $plotBottom
  foreach ($seg in $segments) {
    $h = ($seg.Val / $yMaxA) * $plotH
    $stackTop -= $h
    $brush = New-Object System.Drawing.SolidBrush($seg.Color)
    $g.FillRectangle($brush, $x, $stackTop, $barW, $h)
    $brush.Dispose()
  }
  $icsLbl = "ICS = $($ics[$i].ToString('N0'))"
  $ils = $g.MeasureString($icsLbl, $fVal)
  $g.DrawString($icsLbl, $fVal, $blackBrush, $cx - $ils.Width / 2, $stackTop - $ils.Height - 4)
  $cls = $g.MeasureString($cities[$i], $fLabel)
  $g.DrawString($cities[$i], $fLabel, $blackBrush, $cx - $cls.Width / 2, $plotBottom + 8)
}

$yTitleA = "Weighted capacity score"
$state = $g.Save()
$g.TranslateTransform(18, ($plotTop + $plotBottom) / 2)
$g.RotateTransform(-90)
$yts = $g.MeasureString($yTitleA, $fLabel)
$g.DrawString($yTitleA, $fLabel, $blackBrush, -$yts.Width / 2, 0)
$g.Restore($state)

# Panel B: horizontal bar chart for EVs per capacity unit
DrawPanelTitle "B. EVs per Infrastructure Capacity Unit (lower = better availability)" 406
$plotLeftB = 170; $plotRightB = 1040; $plotTopB = 438; $plotBottomB = 640
$plotWB = $plotRightB - $plotLeftB
$plotHB = $plotBottomB - $plotTopB
$xMaxB = 14.0; $xStepB = 2.0
$barHB = 42
$groupHB = $plotHB / $n

for ($v = 0; $v -le $xMaxB; $v += $xStepB) {
  $x = $plotLeftB + ($v / $xMaxB) * $plotWB
  $g.DrawLine($gridPen, $x, $plotTopB, $x, $plotBottomB)
  $lbl = "$([math]::Round($v,1))"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $plotBottomB + 6)
}
$g.DrawLine($axisPen, $plotLeftB, $plotTopB, $plotLeftB, $plotBottomB)
$g.DrawLine($axisPen, $plotLeftB, $plotBottomB, $plotRightB, $plotBottomB)

for ($i = 0; $i -lt $n; $i++) {
  $cy = $plotTopB + $groupHB * $i + $groupHB / 2
  $y = $cy - $barHB / 2
  $w = ($ratio[$i] / $xMaxB) * $plotWB
  $brush = New-Object System.Drawing.SolidBrush($colorRatio[$i])
  $g.FillRectangle($brush, $plotLeftB, $y, $w, $barHB)
  $brush.Dispose()

  $cityLbl = $cities[$i]
  $cls = $g.MeasureString($cityLbl, $fLabel)
  $g.DrawString($cityLbl, $fLabel, $blackBrush, $plotLeftB - $cls.Width - 12, $cy - $cls.Height / 2)

  $calc = "$($evFleet[$i].ToString('N0')) / $($ics[$i].ToString('N0')) = $($ratio[$i])"
  $rlbl = "$($ratio[$i]) EVs / unit"
  $rls = $g.MeasureString($rlbl, $fVal)
  $g.DrawString($rlbl, $fVal, $blackBrush, $plotLeftB + $w + 8, $cy - $rls.Height / 2)
  $g.DrawString($calc, $fNote, $grayBrush, $plotLeftB + $w + 8, $cy + $rls.Height / 2 + 1)
}

$xTitleB = "EVs per Infrastructure Capacity Unit"
$xts = $g.MeasureString($xTitleB, $fLabel)
$g.DrawString($xTitleB, $fLabel, $blackBrush, ($plotLeftB + $plotRightB) / 2 - $xts.Width / 2, $plotBottomB + 30)

$out = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\ev_per_capacity_unit.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Saved $out"
