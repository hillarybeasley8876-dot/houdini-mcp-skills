param(
    [Parameter(Mandatory=$true)][string]$HoudiniPrefDir,
    [string]$PythonExe,
    [string]$SkillsDir,
    [ValidateRange(1024,65535)][int]$Port = 9877,
    [switch]$Online,
    [switch]$SkipSkills
)
$ErrorActionPreference = 'Stop'
$installArgs = @((Join-Path $PSScriptRoot 'install.py'), '--houdini-pref-dir', $HoudiniPrefDir, '--port', "$Port")
if ($SkillsDir) { $installArgs += @('--skills-dir', $SkillsDir) }
if ($Online) { $installArgs += '--online' }
if ($SkipSkills) { $installArgs += '--skip-skills' }
if ($PythonExe) { & $PythonExe @installArgs }
else { & py -3.12 @installArgs }
if ($LASTEXITCODE -ne 0) { throw "Installation failed (exit $LASTEXITCODE)." }
