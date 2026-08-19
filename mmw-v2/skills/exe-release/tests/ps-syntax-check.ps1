param([string]$Path)
$errors = $null
$tokens = $null
[System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors) | Out-Null
if ($errors.Count -eq 0) { Write-Output "OK"; exit 0 }
foreach ($e in $errors) { Write-Output ("line " + $e.Extent.StartLineNumber + ": " + $e.Message) }
exit 1
