param([Parameter(Mandatory=$true)][string]$ActionsFile)
$ErrorActionPreference = 'Stop'
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class PetInput {
  [StructLayout(LayoutKind.Sequential)] public struct Point { public int X; public int Y; }
  [DllImport("user32.dll")] public static extern bool GetCursorPos(out Point point);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, uint dx, uint dy, uint data, UIntPtr extra);
  [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(Point point);
}
'@
[PetInput]::SetThreadDpiAwarenessContext([IntPtr](-4)) | Out-Null
$original = New-Object PetInput+Point
[PetInput]::GetCursorPos([ref]$original) | Out-Null
try {
    $actions = Get-Content -LiteralPath $ActionsFile -Raw | ConvertFrom-Json
    foreach ($action in $actions) {
        switch ($action.type) {
            'move' {
                $success = [PetInput]::SetCursorPos([int]$action.x, [int]$action.y)
                $position = New-Object PetInput+Point
                [PetInput]::GetCursorPos([ref]$position) | Out-Null
                Write-Output "Move success=$success actual=$($position.X),$($position.Y) hwnd=$([PetInput]::WindowFromPoint($position))"
            }
            'down' { [PetInput]::mouse_event(2,0,0,0,[UIntPtr]::Zero) }
            'up' { [PetInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero) }
            'wait' { Start-Sleep -Milliseconds ([int]$action.ms) }
        }
    }
} finally {
    [PetInput]::mouse_event(4,0,0,0,[UIntPtr]::Zero)
    [PetInput]::SetCursorPos($original.X, $original.Y) | Out-Null
}
