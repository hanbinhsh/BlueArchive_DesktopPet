using System;
using System.Runtime.InteropServices;
using System.Text;

// Receives only wheel messages observed by our own desktop-pet HWND.
// No keyboard hooks, focus changes, global input injection or persisted service.
static class WindowWheel {
    [StructLayout(LayoutKind.Sequential)] struct Point { public int X, Y; }
    [StructLayout(LayoutKind.Sequential)] struct Rect { public int Left, Top, Right, Bottom; }
    delegate bool EnumProc(IntPtr window, IntPtr data);
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc callback, IntPtr data);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr window);
    [DllImport("user32.dll")] static extern bool IsWindowEnabled(IntPtr window);
    [DllImport("user32.dll")] static extern IntPtr WindowFromPoint(Point point);
    [DllImport("user32.dll")] static extern IntPtr GetAncestor(IntPtr window,uint flag);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr window, out Rect rect);
    [DllImport("user32.dll")] static extern IntPtr GetWindowLongPtr(IntPtr window, int index);
    [DllImport("user32.dll")] static extern IntPtr SetWindowLongPtr(IntPtr window, int index, IntPtr value);
    [DllImport("user32.dll")] static extern bool ScreenToClient(IntPtr window, ref Point point);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr window, out uint pid);
    [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr window,StringBuilder name,int length);
    [DllImport("user32.dll")] static extern IntPtr ChildWindowFromPointEx(IntPtr window, Point point, uint flags);
    [DllImport("user32.dll")] static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll", SetLastError=true)] static extern IntPtr SendMessageTimeout(IntPtr window, uint message, UIntPtr wparam, IntPtr lparam, uint flags, uint timeout, out UIntPtr result);
    [DllImport("dwmapi.dll")] static extern int DwmGetWindowAttribute(IntPtr window, uint attribute, out int value, int size);
    static bool Contains(IntPtr window, Point point) {
        Rect r; return GetWindowRect(window, out r) && point.X >= r.Left && point.X < r.Right && point.Y >= r.Top && point.Y < r.Bottom;
    }
    static int Main() {
        SetThreadDpiAwarenessContext(new IntPtr(-4));
        string line;
        while ((line = Console.ReadLine()) != null) {
            try {
                var parts = line.Split(' '); if (parts.Length != 4) continue;
                var excluded = new IntPtr(long.Parse(parts[0])); uint message = uint.Parse(parts[1]);
                uint wp = uint.Parse(parts[2]), lp = uint.Parse(parts[3]);
                if (message != 0x020A && message != 0x020E) continue;
                var point = new Point { X = (short)(lp & 0xffff), Y = (short)(lp >> 16) };
                if (!IsWindowVisible(excluded) || !Contains(excluded, point)) continue;
                bool below = false; IntPtr target = IntPtr.Zero;
                EnumWindows(delegate(IntPtr window, IntPtr data) {
                    if (window == excluded) { below = true; return true; }
                    if (!below || !IsWindowVisible(window) || !IsWindowEnabled(window) || !Contains(window, point)) return true;
                    if ((GetWindowLongPtr(window, -20).ToInt64() & 0x20) != 0) return true;
                    int cloaked; if (DwmGetWindowAttribute(window, 14, out cloaked, 4) == 0 && cloaked != 0) return true;
                    target = window; return false;
                }, IntPtr.Zero);
                if (target == IntPtr.Zero) continue;
                uint owner, source;GetWindowThreadProcessId(target,out owner);GetWindowThreadProcessId(excluded,out source);
                // Chromium routes native wheel messages between widgets on the
                // same UI thread. Use the owning WebContents for our own panels.
                if(owner==source){Console.WriteLine("local "+target.ToInt64()+" "+message+" "+wp+" "+lp);continue;}
                var className=new StringBuilder(256);GetClassName(target,className,256);
                bool chromium=className.ToString().StartsWith("Chrome_WidgetWin_");
                for (int depth = 0; !chromium && depth < 20; depth++) {
                    var local = point; ScreenToClient(target, ref local);
                    var child = ChildWindowFromPointEx(target, local, 7);
                    if (child == IntPtr.Zero || child == target) break;
                    target = child;
                }
                UIntPtr result;
                // Reserved wheel flag marks a forwarded message, preventing
                // a target that bubbles it back from forming a feedback loop.
                // Browsers independently hit-test the pointer and can otherwise
                // reroute the forwarded message back to the overlay. Temporarily
                // use layered click-through for this synchronous dispatch.
                long style=GetWindowLongPtr(excluded,-20).ToInt64();IntPtr sent;
                SetWindowLongPtr(excluded,-20,new IntPtr(style|0x80020));
                var hit=WindowFromPoint(point);
                if(hit!=IntPtr.Zero&&GetAncestor(hit,2)!=excluded)target=chromium?GetAncestor(hit,2):hit;
                if(Environment.GetEnvironmentVariable("BA_TEST_DATA")!=null)Console.WriteLine("probe "+target+" "+WindowFromPoint(point)+" "+className+" "+point.X+","+point.Y);
                try { sent=SendMessageTimeout(target, message, new UIntPtr(wp|0x4000), new IntPtr(unchecked((int)lp)), 2, 250, out result); }
                finally { long current=GetWindowLongPtr(excluded,-20).ToInt64();SetWindowLongPtr(excluded,-20,new IntPtr((current&~0x80020)|(style&0x80020))); }
                Console.WriteLine(sent != IntPtr.Zero ? "forwarded" : "blocked");
            } catch (Exception error) { Console.Error.WriteLine(error.Message); }
        }
        return 0;
    }
}
