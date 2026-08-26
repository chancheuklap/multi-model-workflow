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
. ([scriptblock]::Create((Get-TemplateFunction 'Assert-LicensesShipped')))
. ([scriptblock]::Create((Get-TemplateFunction 'Copy-RuntimeAsset')))

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
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir '__main__.build') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir '__main__.dist\sub') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir '__main__.onefile-build\blobs') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $outDir 'runtime-assets') | Out-Null
  Set-Content -Path (Join-Path $outDir '__main__.build\scons-debug.py') -Value 'x' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir '__main__.dist\sub\lib.pyd') -Value 'x' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir '__main__.onefile-build\blobs\__payload.bin') -Value 'y' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir 'runtime-assets\keep.txt') -Value 'z' -Encoding Ascii
  Set-Content -Path (Join-Path $outDir 'product.exe') -Value 'exe' -Encoding Ascii
  Remove-CompilerIntermediates -OutputDir $outDir
  if ((Test-Path (Join-Path $outDir '__main__.build')) -or
      (Test-Path (Join-Path $outDir '__main__.dist')) -or
      (Test-Path (Join-Path $outDir '__main__.onefile-build'))) {
    no "编译中间目录没被删掉"
  } else {
    ok "编译中间目录被删掉（含 .build：里面是编译器从本产品源码生成的 C）"
  }
  if ((Test-Path (Join-Path $outDir 'product.exe')) -and
      (Test-Path (Join-Path $outDir 'runtime-assets\keep.txt'))) {
    ok "成品与运行时资产原样留着"
  } else {
    no "把不该删的也删了"
  }

  # 许可证随包：闸门认字节，不认路径。成品里换个名字、挪个位置都算到位，删掉才算没到位。
  $licRepo = Join-Path $lab 'licrepo'
  New-Item -ItemType Directory -Force -Path (Join-Path $licRepo 'resources\ffmpeg') | Out-Null
  $licSrc = Join-Path $licRepo 'resources\ffmpeg\LICENSE.txt'
  Set-Content -Path $licSrc -Value 'GPL version 2 or later, the whole text' -Encoding Ascii
  $pkg = Join-Path $lab 'packaged'
  New-Item -ItemType Directory -Force -Path (Join-Path $pkg 'resources\app\vendor') | Out-Null
  Copy-Item -LiteralPath $licSrc -Destination (Join-Path $pkg 'resources\app\vendor\ffmpeg-LICENSE.txt')
  Set-Content -Path (Join-Path $pkg 'app.exe') -Value 'not a licence' -Encoding Ascii
  try {
    Assert-LicensesShipped -Licenses @(@{Name = 'ffmpeg'; Path = 'resources/ffmpeg/LICENSE.txt'}) -RepoRoot $licRepo -PackageDir $pkg
    ok "许可证改了名字挪了位置，只要字节在包里就算随包出厂"
  } catch {
    no ("许可证在包里却被判成没到位：" + $_.Exception.Message)
  }
  Remove-Item -LiteralPath (Join-Path $pkg 'resources\app\vendor\ffmpeg-LICENSE.txt') -Force
  try {
    Assert-LicensesShipped -Licenses @(@{Name = 'ffmpeg'; Path = 'resources/ffmpeg/LICENSE.txt'}) -RepoRoot $licRepo -PackageDir $pkg
    no "许可证被打包过滤掉了却没被拦下"
  } catch {
    if ($_.Exception.Message -like '*without*') {
      ok "许可证被打包过滤掉，出包停下"
    } else {
      no ("拦下了但说的不是这件事：" + $_.Exception.Message)
    }
  }
  # ── 随包但不嵌入的数据 ────────────────────────────────────────────────────
  #
  # 从包目录取成员那一种要问真解释器要位置，本机不一定有那个包，所以这里只验不依赖
  # 解释器的三条；那一种由真实出包做端到端证明。
  $raRepo = Join-Path $lab 'ra-repo'
  $raSrc = Join-Path $raRepo 'runtime-assets\app\assets'
  New-Item -ItemType Directory -Force -Path (Join-Path $raSrc 'bgm') | Out-Null
  Set-Content -Path (Join-Path $raSrc 'manifest.json') -Value '{}' -Encoding Ascii
  Set-Content -Path (Join-Path $raSrc 'bgm\track.mp3') -Value 'AUDIO' -Encoding Ascii
  $raDest = Join-Path $lab 'ra-out\app\assets'
  try {
    Copy-RuntimeAsset -Source 'runtime-assets/app/assets' -Dest $raDest -RepoRoot $raRepo -Label 'app/assets'
    if ((Test-Path -LiteralPath (Join-Path $raDest 'bgm\track.mp3')) -and
        (Test-Path -LiteralPath (Join-Path $raDest 'manifest.json'))) {
      ok "仓库里的资产目录整棵拷到落点"
    } else {
      no "拷过去了但文件不在落点"
    }
  } catch {
    no ("仓库源拷贝报错：" + $_.Exception.Message)
  }

  # 落点已有别人写进去的东西（产品钩子抓下来的曲子）时，这一步只叠加不清空——
  # 清空会把同一棵树里兄弟步骤的成果删掉，而两边都不会报错。
  Set-Content -Path (Join-Path $raDest 'bgm\fetched.mp3') -Value 'FETCHED' -Encoding Ascii
  try {
    Copy-RuntimeAsset -Source 'runtime-assets/app/assets' -Dest $raDest -RepoRoot $raRepo -Label 'app/assets'
    if (Test-Path -LiteralPath (Join-Path $raDest 'bgm\fetched.mp3')) {
      ok "再拷一次不清空落点，钩子先放进去的东西还在"
    } else {
      no "第二次拷贝把钩子放进去的文件删了"
    }
  } catch {
    no ("重复拷贝报错：" + $_.Exception.Message)
  }

  try {
    Copy-RuntimeAsset -Source 'runtime-assets/app/nope' -Dest (Join-Path $lab 'ra-out2') -RepoRoot $raRepo -Label 'app/nope'
    no "源在仓库里根本不存在却没被拦下"
  } catch {
    if ($_.Exception.Message -like '*no source in the repository*') {
      ok "源不在仓库里，出包停下"
    } else {
      no ("拦下了但说的不是这件事：" + $_.Exception.Message)
    }
  }

  # 从包目录取成员那一种：用构建机上的 python 和标准库的 json 包代替产品的真实依赖，
  # 验的是「解析包目录 → 取点名的成员 → 落地」这条链，不是某个具体的包。
  #
  # 这一条本来被跳过了，理由是「留给真实出包做端到端证明」——而它第一次真实出包就炸了：
  # runner 多半是 `uv run --extra …`，不在项目目录里跑，uv 会打一句 warning 到 stderr；
  # 当时的实现用 2>&1 捕获输出，那句 warning 变成 ErrorRecord，把整步判成失败。
  $pkgDest = Join-Path $lab 'ra-pkg'
  try {
    Copy-RuntimeAsset -SourcePackage 'json' -Members @('decoder.py') -Dest $pkgDest -RepoRoot $lab -Runner @('python') -Label 'probe/json'
    if (Test-Path -LiteralPath (Join-Path $pkgDest 'decoder.py')) {
      ok "按包名解析出包目录，点名的成员落到位"
    } else {
      no "解析成功但成员没落地"
    }
  } catch {
    no ("从包目录取成员报错：" + $_.Exception.Message)
  }

  try {
    Copy-RuntimeAsset -SourcePackage 'no_such_package_xyzzy' -Members @('x.py') -Dest (Join-Path $lab 'ra-pkg2') -RepoRoot $lab -Runner @('python') -Label 'probe/missing'
    no "包在编译环境里根本没有却没被拦下"
  } catch {
    # 断言认的是「解析不出这个包」这件事，不是随便什么异常——catch 得太宽，
    # 上一条里那个 & 传参的错也会在这里冒充成功。
    if ($_.Exception.Message -like '*Could not locate the package*') {
      ok "包不在编译环境里，出包停下"
    } else {
      no ("拦下了但说的不是这件事：" + $_.Exception.Message)
    }
  }

  # 拷贝跑完了和数据在包里是两件事：源目录是空的，Copy-Item 一声不吭地成功。
  $emptySrc = Join-Path $raRepo 'runtime-assets\app\empty'
  New-Item -ItemType Directory -Force -Path $emptySrc | Out-Null
  try {
    Copy-RuntimeAsset -Source 'runtime-assets/app/empty' -Dest (Join-Path $lab 'ra-out3') -RepoRoot $raRepo -Label 'app/empty'
    no "一个文件都没拷进去却报成功"
  } catch {
    if ($_.Exception.Message -like '*copied nothing*') {
      ok "拷贝跑完但落点是空的，出包停下"
    } else {
      no ("拦下了但说的不是这件事：" + $_.Exception.Message)
    }
  }
}
finally {
  Remove-Item -Recurse -Force $lab -ErrorAction SilentlyContinue
}

Write-Host ("=== " + $pass + " PASS / " + $fail + " FAIL ===")
if ($fail -gt 0) { exit 1 }
