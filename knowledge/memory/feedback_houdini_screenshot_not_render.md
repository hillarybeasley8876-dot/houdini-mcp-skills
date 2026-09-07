---
name: houdini-screenshot-not-render
description: "For Houdini visual verification, take a Windows screenshot of the viewport — never call MCP render tools (they crash hindie repeatedly)"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 4a8f3014-d692-429a-910c-2cb38ff3bd3a
---

When the user wants to see the result of a Houdini build, take a Windows desktop/window screenshot — do NOT call `mcp__houdini__render_*` tools.

**Why:** `render_specific_camera` and `render_quad_views` both crashed `hindie.exe` mid-call multiple times in this session, even after the geometry cooked cleanly. Each crash burns several minutes on relaunch + hip reload + state recovery. The user explicitly said "你直接拍屏不就行了" — they consider the renderer roundtrip wasted effort when the viewport already shows the answer.

**How to apply:** After a build/edit cooks successfully, frame the geometry in the SceneViewer (set camera + viewport flag), then capture via PowerShell:

```powershell
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$proc = Get-Process hindie -ErrorAction SilentlyContinue | Select-Object -First 1
if ($proc) {
    $hwnd = $proc.MainWindowHandle
    Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Drawing;
public class W {
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L,T,R,B; }
}
"@
    [W]::SetForegroundWindow($hwnd) | Out-Null
    Start-Sleep -Milliseconds 400
    $r = New-Object W+RECT
    [W]::GetWindowRect($hwnd, [ref]$r) | Out-Null
    $w = $r.R - $r.L; $h = $r.B - $r.T
    $bmp = New-Object System.Drawing.Bitmap $w, $h
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
    $bmp.Save('C:/Users/nieyi/work/houdini_capture.png')
}
```

Then `Read` the saved PNG.

If the user wants quad views, snapshot once per camera angle (set viewport camera between snaps), not via the render tool.
