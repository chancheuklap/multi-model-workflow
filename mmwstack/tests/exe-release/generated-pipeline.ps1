param([Parameter(Mandatory = $true)][string]$Path)

$ErrorActionPreference = 'Stop'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors -join '; ') }

function Get-ExpressionFacts($node) {
  @{
    strings = @($node.FindAll({
      param($n)
      $n -is [System.Management.Automation.Language.StringConstantExpressionAst] -or
      $n -is [System.Management.Automation.Language.ExpandableStringExpressionAst]
    }, $false) | ForEach-Object { $_.Value })
    variables = @($node.FindAll({
      param($n)
      $n -is [System.Management.Automation.Language.VariableExpressionAst]
    }, $false) | ForEach-Object { $_.VariablePath.UserPath })
  }
}

# Inspect the generated entry point, not helper definitions. Do not execute it.
$commands = @($ast.EndBlock.FindAll({
  param($n)
  $n -is [System.Management.Automation.Language.CommandAst]
}, $false) | ForEach-Object {
  $cmd = $_
  $named = @{}
  $positional = @()
  $key = $null
  foreach ($arg in ($cmd.CommandElements | Select-Object -Skip 1)) {
    if ($arg -is [System.Management.Automation.Language.CommandParameterAst]) {
      $key = $arg.ParameterName
      $named[$key] = $null
      if ($arg.Argument) {
        $named[$key] = Get-ExpressionFacts $arg.Argument
        $key = $null
      }
    } elseif ($key) {
      $named[$key] = Get-ExpressionFacts $arg
      $key = $null
    } else {
      $positional += Get-ExpressionFacts $arg
    }
  }
  @{
    name = $cmd.GetCommandName()
    named = $named
    positional = $positional
    offset = $cmd.Extent.StartOffset
  }
})
$assignments = @($ast.EndBlock.FindAll({
  param($n)
  $n -is [System.Management.Automation.Language.AssignmentStatementAst] -and
  $n.Left -is [System.Management.Automation.Language.VariableExpressionAst]
}, $false) | ForEach-Object {
  @{
    variable = $_.Left.VariablePath.UserPath
    value = Get-ExpressionFacts $_.Right
    offset = $_.Extent.StartOffset
  }
})
@{commands = $commands; assignments = $assignments} | ConvertTo-Json -Depth 12 -Compress
