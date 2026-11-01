param([Parameter(Mandatory=$true)][string]$Path)
$sig = Get-AuthenticodeSignature -FilePath $Path
if ($sig.Status -ne 'Valid') { Write-Error "Invalid Authenticode signature: $($sig.Status)"; exit 1 }
Write-Host "Valid Authenticode signature: $($sig.SignerCertificate.Subject)"
