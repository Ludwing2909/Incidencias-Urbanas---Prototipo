param([Parameter(Mandatory=$true)][string]$InputDocx,[Parameter(Mandatory=$true)][string]$OutputPdf)
$ErrorActionPreference = 'Stop'
$wordInstance = $null
$documentInstance = $null
try {
    $wordInstance = New-Object -ComObject Word.Application
    $wordInstance.Visible = $false
    $wordInstance.DisplayAlerts = 0
    $documentInstance = $wordInstance.Documents.Open($InputDocx, $false, $false)
    $documentInstance.Fields.Update() | Out-Null
    foreach ($tocInstance in $documentInstance.TablesOfContents) { $tocInstance.Update() }
    $documentInstance.Repaginate()
    foreach ($tocInstance in $documentInstance.TablesOfContents) { $tocInstance.UpdatePageNumbers() }
    $documentInstance.Save()
    $documentInstance.ExportAsFixedFormat($OutputPdf, 17)
    Write-Output ('Documento renderizado con Word. Páginas: ' + $documentInstance.ComputeStatistics(2))
}
finally {
    if ($documentInstance) { $documentInstance.Close(0); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($documentInstance) }
    if ($wordInstance) { $wordInstance.Quit(); [void][System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($wordInstance) }
}
