# 在构建机上验模板里那几个守卫函数的**行为**，不是语法。
#
# Mac 上没有 PowerShell，所以这一份跟 ps-syntax-check.ps1 一样送到构建机上跑。语法过了不
# 代表判得对：源码泄漏扫描曾经两次误报——先按名字比，后按路径后缀比——每次都挡下了一个
# 本来没问题的发布，而两次都是语法完全正确的代码。
#
# 用法：powershell -File template-behaviour.ps1 -Template <nuitka_electron.ps1.tmpl>

param([Parameter(Mandatory = $true)][string]$Template)

$ErrorActionPreference = 'Stop'
# 中文机的控制台是 GBK，这份文件是 UTF-8：两头都钉成 UTF-8，输出才不是乱码。
try {
  [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
  $OutputEncoding = [Text.UTF8Encoding]::new($false)
} catch { }
$pass = 0
$fail = 0
function ok($m) { Write-Host ("  PASS: " + $m); $script:pass++ }
function no($m) { Write-Host ("  FAIL: " + $m); $script:fail++ }

# 模板里的函数都从第 0 列开始，到第 0 列的 } 结束。这里只取要验的那几个。
$text = Get-Content -LiteralPath $Template -Raw
function Get-TemplateFunction([string]$name) {
  $pattern = "(?ms)^function\s+$name\s*\{.*?^\}"
  $m = [regex]::Match($text, $pattern)
  if (-not $m.Success) { throw "the template holds no function $name" }
  return $m.Value
}

# 点源在脚本作用域，函数才留得住——在别的函数里 Invoke-Expression，出了那个函数就没了。
. ([scriptblock]::Create((Get-TemplateFunction 'Assert-NoBusinessSource')))
. ([scriptblock]::Create((Get-TemplateFunction 'Assert-DistinctExeTails')))
. ([scriptblock]::Create((Get-TemplateFunction 'Remove-CompilerIntermediates')))

$lab = Join-Path $env:TEMP ("mmw-template-behaviour-" + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $lab | Out-Null
try {
  # 一个仓库：src/shared 与 src/parrot_dubbing 都是这个产品自己的包。
  $RepoRoot = Join-Path $lab 'repo'
  foreach ($d in @('src\shared', 'src\parrot_dubbing\api')) {
    New-Item -ItemType Directory -Force -Path (Join-Path $RepoRoot $d) | Out-Null
  }
  Set-Content -Path (Join-Path $RepoRoot 'src\shared\__init__.py') -Value '' -Encoding Ascii
  Set-Content -Path (Join-Path $RepoRoot 'src\parrot_dubbing\__init__.py') -Value '' -Encoding Ascii
  Set-Content -Path (Join-Path $RepoRoot 'src\parrot_dubbing\api\__init__.py') -Value '' -Encoding Ascii
  Set-Content -Path (Join-Path $RepoRoot 'src\parrot_dubbing\api\app.py') -Value '# business' -Encoding Ascii

  # 一个出货树：只有第三方。openai 里正好有个叫 shared 的子包。
  $dist = Join-Path $lab 'dist'
  $sp = Join-Path $dist 'python-runtime\Lib\site-packages'
  New-Item -ItemType Directory -Force -Path (Join-Path $sp 'openai\types\shared') | Out-Null
  foreach ($f in @('openai\__init__.py', 'openai\types\__init__.py', 'openai\types\shared\__init__.py')) {
    Set-Content -Path (Join-Path $sp $f) -Value '# third party' -Encoding Ascii
  }

  try {
    Assert-NoBusinessSource -Roots @($dist) -SourceRoots @('src')
    ok "第三方包里同名的 shared 子包不算泄漏"
  } catch {
    no ("第三方 openai/types/shared 被误判成业务源码：" + $_.Exception.Message)
  }

  # 真泄漏：这个产品自己的包原样进了出货树。
  New-Item -ItemType Directory -Force -Path (Join-Path $sp 'parrot_dubbing\api') | Out-Null
  foreach ($f in @('parrot_dubbing\__init__.py', 'parrot_dubbing\api\__init__.py')) {
    Set-Content -Path (Join-Path $sp $f) -Value '' -Encoding Ascii
  }
  Set-Content -Path (Join-Path $sp 'parrot_dubbing\api\app.py') -Value '# business' -Encoding Ascii
  try {
    Assert-NoBusinessSource -Roots @($dist) -SourceRoots @('src')
    no "业务源码真的进了包却没被拦下"
  } catch {
    if ($_.Exception.Message -like '*parrot_dubbing*app.py*') {
      ok "业务源码进包被拦下，并指出是哪个文件"
    } else {
      no ("拦下了但说的不是那个文件：" + $_.Exception.Message)
    }
  }

  # 顶层单文件模块：仓库里的 src/settings.py 进了包算泄漏，第三方的同名文件不算。
  Set-Content -Path (Join-Path $RepoRoot 'src\settings.py') -Value '# business' -Encoding Ascii
  Set-Content -Path (Join-Path $sp 'openai\settings.py') -Value '# third party' -Encoding Ascii
  Remove-Item -Recurse -Force (Join-Path $sp 'parrot_dubbing')
  try {
    Assert-NoBusinessSource -Roots @($dist) -SourceRoots @('src')
    ok "第三方包里的同名单文件不算泄漏"
  } catch {
    no ("第三方 openai/settings.py 被误判：" + $_.Exception.Message)
  }
  Set-Content -Path (Join-Path $sp 'settings.py') -Value '# business' -Encoding Ascii
  try {
    Assert-NoBusinessSource -Roots @($dist) -SourceRoots @('src')
    no "顶层单文件模块进包却没被拦下"
  } catch {
    ok "顶层单文件模块进包被拦下"
  }

  # --remove-output 把 payload 目录删了之后走的兜底：两个 exe 的尾巴一样就是同一个 payload。
  $exeDir = Join-Path $lab 'exes'
  New-Item -ItemType Directory -Force -Path $exeDir | Out-Null
  $head = New-Object byte[] 4096
  $tailA = New-Object byte[] 16384
  $tailB = New-Object byte[] 16384
  for ($i = 0; $i -lt 4096; $i++) { $head[$i] = [byte]($i % 251) }
  for ($i = 0; $i -lt 16384; $i++) { $tailA[$i] = [byte]($i % 253) }
  for ($i = 0; $i -lt 16384; $i++) { $tailB[$i] = [byte](($i * 7 + 3) % 241) }
  $one = Join-Path $exeDir 'one.exe'
  $two = Join-Path $exeDir 'two.exe'
  [IO.File]::WriteAllBytes($one, ($head + $tailA))
  [IO.File]::WriteAllBytes($two, ($head + $tailB))
  try {
    Assert-DistinctExeTails -Exes @($one, $two)
    ok "两个 exe 各带各的 payload 时放行"
  } catch {
    no ("两个不同的 exe 被误判成同一个 payload：" + $_.Exception.Message)
  }
  [IO.File]::WriteAllBytes($two, ($head + $tailA))
  try {
    Assert-DistinctExeTails -Exes @($one, $two)
    no "两个 exe 带同一个 payload 却没被拦下"
  } catch {
    if ($_.Exception.Message -like '*same bytes*') {
      ok "两个 exe 带同一个 payload 被拦下"
    } else {
      no ("拦下了但说的不是这件事：" + $_.Exception.Message)
    }
  }

  # 编译中间产物：<入口>.dist 与 <入口>.onefile-build 删掉，成品 exe 留着。
  $outDir = Join-Path $lab 'compiled'
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir '__main__.dist\sub') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir '__main__.onefile-build\blobs') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir 'runtime-assets') | Out-Null
  Set-Content -Path (Join-Path $outDir '__main__.dist\sub\lib.pyd') -Value 'x' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir '__main__.onefile-build\blobs\__payload.bin') -Value 'y' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir 'runtime-assets\keep.txt') -Value 'z' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir 'product.exe') -Value 'exe' -Encoding Ascii
  Remove-CompilerIntermediates -OutputDir $outDir
  if ((Test-Path (Join-Path $outDir '__main__.dist')) -or
      (Test-Path (Join-Path $outDir '__main__.onefile-build'))) {
    no "编译中间目录没被删掉"
  } else {
    ok "编译中间目录被删掉"
  }
  if ((Test-Path (Join-Path $outDir 'product.exe')) -and
      (Test-Path (Join-Path $outDir 'runtime-assets\keep.txt'))) {
    ok "成品与运行时资产原样留着"
  } else {
    no "把不该删的也删了"
  }
}
finally {
  Remove-Item -Recurse -Force $lab -ErrorAction SilentlyContinue
}

Write-Host ("=== " + $pass + " PASS / " + $fail + " FAIL ===")
if ($fail -gt 0) { exit 1 }
