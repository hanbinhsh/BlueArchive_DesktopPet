import {contextBridge,ipcRenderer} from 'electron';
contextBridge.exposeInMainWorld('range',{command:(name:string,value?:number)=>ipcRenderer.send('range:command',name,value),onState:(fn:(v:{radius:number;actual:number})=>void)=>ipcRenderer.on('range:state',(_e,v)=>fn(v))});
