"""Inspect authored D3D shaders locally; no game process or executable is modified.

API: https://learn.microsoft.com/windows/win32/api/d3dcompiler/nf-d3dcompiler-d3ddisassemble
"""
import ctypes as C
import pathlib

dll=C.WinDLL('d3dcompiler_47.dll')
disassemble=dll.D3DDisassemble
disassemble.argtypes=[C.c_void_p,C.c_size_t,C.c_uint,C.c_char_p,C.POINTER(C.c_void_p)]
disassemble.restype=C.c_long
for p in pathlib.Path('.assets/water-shaders').glob('*.dxbc'):
    raw=p.read_bytes();blob=C.c_void_p()
    result=disassemble(raw,len(raw),0,None,C.byref(blob))
    if result:raise OSError(result,p.name)
    table=C.cast(blob,C.POINTER(C.POINTER(C.c_void_p))).contents
    pointer=C.WINFUNCTYPE(C.c_void_p,C.c_void_p)(table[3])(blob)
    size=C.WINFUNCTYPE(C.c_size_t,C.c_void_p)(table[4])(blob)
    p.with_suffix('.txt').write_bytes(C.string_at(pointer,size).rstrip(b'\0'))
    C.WINFUNCTYPE(C.c_ulong,C.c_void_p)(table[2])(blob)
print('Disassembled local FX programs')
