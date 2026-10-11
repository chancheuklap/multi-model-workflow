param([string]$Path)

# 两件事：脚本能不能解析，以及它调用的每个命令是不是真的存在。
#
# 只验语法漏掉过一次真事故：改模板时整段替换，把夹在中间的两个函数一起删了，而生成的脚本
# 仍然在调用它们——语法完全正确，构建机跑到那一行才炸，四十分钟没了。
#
# 这里不维护任何名单：脚本自己定义的函数从 AST 里拿，其余交给 Get-Command 去查。
$errors = $null
$tokens = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) {
  foreach ($e in $errors) { Write-Output ("line " + $e.Extent.StartLineNumber + ": " + $e.Message) }
  exit 1
}

$defined = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
foreach ($fn in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] }, $true)) {
  [void]$defined.Add($fn.Name)
}

$missing = @{}
foreach ($cmd in $ast.FindAll({ param($n) $n -is [System.Management.Automation.Language.CommandAst] }, $true)) {
  $name = $cmd.GetCommandName()
  # 名字要到运行时才知道的（& $var）这里判不了，跳过。
  if (-not $name) { continue }
  if ($defined.Contains($name)) { continue }
  if (Get-Command -Name $name -ErrorAction SilentlyContinue) { continue }
  if (-not $missing.ContainsKey($name)) { $missing[$name] = $cmd.Extent.StartLineNumber }
}

if ($missing.Count -gt 0) {
  foreach ($name in $missing.Keys) {
    Write-Output ("line " + $missing[$name] + ": calls '" + $name + "', which this script does not define and this machine does not have")
  }
  exit 1
}
Write-Output "OK"
exit 0
