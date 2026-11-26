Add-Type -AssemblyName System.Drawing

$cities = @("Helsinki", "Tampere", "Oulu")
$temp   = @(-5.15, -5.98, -8.90)
$factor = @(1.26, 1.30, 1.45)

$colorTemp = @(
  [System.Drawing.Color]::FromArgb(59, 130, 246),
  [System.Drawing.Color]::FromArgb(37, 99, 235),
  [System.Drawing.Color]::FromArgb(29, 78, 216)
)
$colorFactor = @(
  [System.Drawing.Color]::FromArgb(251, 146, 60),
  [System.Drawing.Color]::FromArgb(249, 115, 22),
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
$fNote  = New-Object System.Drawing.Font("Segoe UI", 8.5)
$blackBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(26, 26, 26))
$grayBrush  = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(90, 90, 90))
$gridPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(230, 230, 230), 1)
$axisPen = New-Object System.Drawing.Pen([System.Drawing.Color]::FromArgb(150, 150, 150), 1)

$title = "Climate Severity Factor by Municipality"
$ts = $g.MeasureString($title, $fTitle)
$g.DrawString($title, $fTitle, $blackBrush, ($W - $ts.Width) / 2, 14)

$sub = "Climate Factor = 1 + |Average January Temperature| / 20   |   Higher value = more severe winter conditions"
$ss = $g.MeasureString($sub, $fSub)
$g.DrawString($sub, $fSub, $grayBrush, ($W - $ss.Width) / 2, 40)

function DrawPanelTitle($text, $y) {
  $size = $g.MeasureString($text, $fPanel)
  $g.DrawString($text, $fPanel, $blackBrush, ($W - $size.Width) / 2, $y)
}

$n = $cities.Count

# Panel A: January temperature (horizontal bars, negative values)
DrawPanelTitle "A. Average January Temperature (2010-2025)" 72
$plotLeftA = 170; $plotRightA = 1040; $plotTopA = 102; $plotBottomA = 310
$plotWA = $plotRightA - $plotLeftA
$plotHA = $plotBottomA - $plotTopA
$xMinA = -10.0; $xMaxA = 0.0
$barHA = 42
$groupHA = $plotHA / $n

for ($v = $xMinA; $v -le $xMaxA; $v += 2.0) {
  $x = $plotLeftA + (($v - $xMinA) / ($xMaxA - $xMinA)) * $plotWA
  $g.DrawLine($gridPen, $x, $plotTopA, $x, $plotBottomA)
  $lbl = "$([math]::Round($v,1))"
  $ls = $g.MeasureString($lbl, $fAxis)
  $g.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $plotBottomA + 6)
}
$g.DrawLine($axisPen, $plotLeftA, $plotTopA, $plotLeftA, $plotBottomA)
$g.DrawLine($axisPen, $plotLeftA, $plotBottomA, $plotRightA, $plotBottomA)

for ($i = 0; $i -lt $n; $i++) {
  $cy = $plotTopA + $groupHA * $i + $groupHA / 2
  $y = $cy - $barHA / 2
  $zeroX = $plotLeftA + ((0 - $xMinA) / ($xMaxA - $xMinA)) * $plotWA
  $endX  = $plotLeftA + (($temp[$i] - $xMinA) / ($xMaxA - $xMinA)) * $plotWA
  $x = [Math]::Min($zeroX, $endX)
  $w = [Math]::Abs($endX - $zeroX)
  $brush = New-Object System.Drawing.SolidBrush($colorTemp[$i])
  $g.FillRectangle($brush, $x, $y, $w, $barHA)
  $brush.Dispose()

  $cityLbl = $cities[$i]
  $cls = $g.MeasureString($cityLbl, $fLabel)
  $g.DrawString($cityLbl, $fLabel, $blackBrush, $plotLeftA - $cls.Width - 12, $cy - $cls.Height / 2)

  $tlbl = "$($temp[$i]) C"
  $tls = $g.MeasureString($tlbl, $fVal)
  $g.DrawString($tlbl, $fVal, $blackBrush, $endX - $tls.Width - 6, $cy - $tls.Height / 2)
}

$xTitleA = "Average January temperature (C)"
$xtsA = $g.MeasureString($xTitleA, $fLabel)
$g.DrawString($xTitleA, $fLabel, $blackBrush, ($plotLeftA + $plotRightA) / 2 - $xtsA.Width / 2, $plotBottomA + 30)

# Panel B: Climate Factor (horizontal bars)
DrawPanelTitle "B. Climate Severity Factor" 356
$plotLeftB = 170; $plotRightB = 1040; $plotTopB = 388; $plotBottomB = 600
$plotWB = $plotRightB - $plotLeftB
$plotHB = $plotBottomB - $plotTopB
$xMinB = 1.0; $xMaxB = 1.5
$barHB = 42
$groupHB = $plotHB / $n

for ($v = $xMinB; $v -le $xMaxB; $v += 0.1) {
  $x = $plotLeftB + (($v - $xMinB) / ($xMaxB - $xMinB)) * $plotWB
  $g.DrawLine($gridPen, $x, $plotTopB, $x, $plotBottomB)
  if ([Math]::Round($v, 1) % 0.2 -lt 0.05) {
    $lbl = "$([math]::Round($v,1))"
    $ls = $g.MeasureString($lbl, $fAxis)
    $g.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $plotBottomB + 6)
  }
}
$g.DrawLine($axisPen, $plotLeftB, $plotTopB, $plotLeftB, $plotBottomB)
$g.DrawLine($axisPen, $plotLeftB, $plotBottomB, $plotRightB, $plotBottomB)

for ($i = 0; $i -lt $n; $i++) {
  $cy = $plotTopB + $groupHB * $i + $groupHB / 2
  $y = $cy - $barHB / 2
  $w = (($factor[$i] - $xMinB) / ($xMaxB - $xMinB)) * $plotWB
  $brush = New-Object System.Drawing.SolidBrush($colorFactor[$i])
  $g.FillRectangle($brush, $plotLeftB, $y, $w, $barHB)
  $brush.Dispose()

  $cityLbl = $cities[$i]
  $cls = $g.MeasureString($cityLbl, $fLabel)
  $g.DrawString($cityLbl, $fLabel, $blackBrush, $plotLeftB - $cls.Width - 12, $cy - $cls.Height / 2)

  $absT = [Math]::Abs($temp[$i])
  $calc = "1 + $absT / 20 = $($factor[$i])"
  $flbl = "$($factor[$i])"
  $fls = $g.MeasureString($flbl, $fVal)
  $g.DrawString($flbl, $fVal, $blackBrush, $plotLeftB + $w + 8, $cy - $fls.Height / 2)
  $g.DrawString($calc, $fNote, $grayBrush, $plotLeftB + $w + 8, $cy + $fls.Height / 2 + 1)
}

$xTitleB = "Climate Factor"
$xtsB = $g.MeasureString($xTitleB, $fLabel)
$g.DrawString($xTitleB, $fLabel, $blackBrush, ($plotLeftB + $plotRightB) / 2 - $xtsB.Width / 2, $plotBottomB + 30)

$out = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\climate_factor.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Host "Saved $out"

function SaveStandalone($panel) {
  $sW = 900; $sH = 420
  $sbmp = New-Object System.Drawing.Bitmap($sW, $sH)
  $sg = [System.Drawing.Graphics]::FromImage($sbmp)
  $sg.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
  $sg.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::ClearTypeGridFit
  $sg.Clear([System.Drawing.Color]::White)

  if ($panel -eq "temp") {
    $st = "Average January Temperature by Municipality (2010-2025)"
    $sts = $sg.MeasureString($st, $fTitle)
    $sg.DrawString($st, $fTitle, $blackBrush, ($sW - $sts.Width) / 2, 14)
    $ssub = "Input data for Climate Factor calculation"
    $sss = $sg.MeasureString($ssub, $fSub)
    $sg.DrawString($ssub, $fSub, $grayBrush, ($sW - $sss.Width) / 2, 40)

    $pL = 150; $pR = 840; $pT = 78; $pB = 340
    $pW = $pR - $pL; $pH = $pB - $pT
    $xMin = -10.0; $xMax = 0.0
    for ($v = $xMin; $v -le $xMax; $v += 2.0) {
      $x = $pL + (($v - $xMin) / ($xMax - $xMin)) * $pW
      $sg.DrawLine($gridPen, $x, $pT, $x, $pB)
      $lbl = "$([math]::Round($v,1))"
      $ls = $sg.MeasureString($lbl, $fAxis)
      $sg.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $pB + 6)
    }
    $sg.DrawLine($axisPen, $pL, $pT, $pL, $pB)
    $sg.DrawLine($axisPen, $pL, $pB, $pR, $pB)
    $gH = $pH / $n; $bH = 46
    for ($i = 0; $i -lt $n; $i++) {
      $cy = $pT + $gH * $i + $gH / 2
      $zeroX = $pL + ((0 - $xMin) / ($xMax - $xMin)) * $pW
      $endX  = $pL + (($temp[$i] - $xMin) / ($xMax - $xMin)) * $pW
      $x = [Math]::Min($zeroX, $endX); $w = [Math]::Abs($endX - $zeroX)
      $brush = New-Object System.Drawing.SolidBrush($colorTemp[$i])
      $sg.FillRectangle($brush, $x, $cy - $bH/2, $w, $bH); $brush.Dispose()
      $cls = $sg.MeasureString($cities[$i], $fLabel)
      $sg.DrawString($cities[$i], $fLabel, $blackBrush, $pL - $cls.Width - 12, $cy - $cls.Height/2)
      $tlbl = "$($temp[$i]) C"; $tls = $sg.MeasureString($tlbl, $fVal)
      $sg.DrawString($tlbl, $fVal, $blackBrush, $endX - $tls.Width - 6, $cy - $tls.Height/2)
    }
    $xt = "Average January temperature (C)"
    $xts = $sg.MeasureString($xt, $fLabel)
    $sg.DrawString($xt, $fLabel, $blackBrush, ($pL + $pR)/2 - $xts.Width/2, $pB + 30)
    $path = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\climate_january_temperature.png"
  } else {
    $st = "Climate Severity Factor by Municipality"
    $sts = $sg.MeasureString($st, $fTitle)
    $sg.DrawString($st, $fTitle, $blackBrush, ($sW - $sts.Width) / 2, 14)
    $ssub = "Climate Factor = 1 + |Average January Temperature| / 20"
    $sss = $sg.MeasureString($ssub, $fSub)
    $sg.DrawString($ssub, $fSub, $grayBrush, ($sW - $sss.Width) / 2, 40)

    $pL = 150; $pR = 840; $pT = 78; $pB = 340
    $pW = $pR - $pL; $pH = $pB - $pT
    $xMin = 1.0; $xMax = 1.5
    for ($v = $xMin; $v -le $xMax; $v += 0.1) {
      $x = $pL + (($v - $xMin) / ($xMax - $xMin)) * $pW
      $sg.DrawLine($gridPen, $x, $pT, $x, $pB)
      if ([Math]::Round($v, 1) % 0.2 -lt 0.05) {
        $lbl = "$([math]::Round($v,1))"
        $ls = $sg.MeasureString($lbl, $fAxis)
        $sg.DrawString($lbl, $fAxis, $grayBrush, $x - $ls.Width / 2, $pB + 6)
      }
    }
    $sg.DrawLine($axisPen, $pL, $pT, $pL, $pB)
    $sg.DrawLine($axisPen, $pL, $pB, $pR, $pB)
    $gH = $pH / $n; $bH = 46
    for ($i = 0; $i -lt $n; $i++) {
      $cy = $pT + $gH * $i + $gH / 2
      $w = (($factor[$i] - $xMin) / ($xMax - $xMin)) * $pW
      $brush = New-Object System.Drawing.SolidBrush($colorFactor[$i])
      $sg.FillRectangle($brush, $pL, $cy - $bH/2, $w, $bH); $brush.Dispose()
      $cls = $sg.MeasureString($cities[$i], $fLabel)
      $sg.DrawString($cities[$i], $fLabel, $blackBrush, $pL - $cls.Width - 12, $cy - $cls.Height/2)
      $absT = [Math]::Abs($temp[$i])
      $calc = "1 + $absT / 20 = $($factor[$i])"
      $flbl = "$($factor[$i])"; $fls = $sg.MeasureString($flbl, $fVal)
      $sg.DrawString($flbl, $fVal, $blackBrush, $pL + $w + 8, $cy - $fls.Height/2)
      $sg.DrawString($calc, $fNote, $grayBrush, $pL + $w + 8, $cy + $fls.Height/2 + 1)
    }
    $xt = "Climate Factor"
    $xts = $sg.MeasureString($xt, $fLabel)
    $sg.DrawString($xt, $fLabel, $blackBrush, ($pL + $pR)/2 - $xts.Width/2, $pB + 30)
    $path = "C:\Users\jshaji\Documents\Thesis\EV_Data_code\climate_factor_score.png"
  }

  $sbmp.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
  $sg.Dispose(); $sbmp.Dispose()
  Write-Host "Saved $path"
}

SaveStandalone "temp"
SaveStandalone "factor"
