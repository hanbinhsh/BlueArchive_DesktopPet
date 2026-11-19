import {contextBridge,ipcRenderer} from 'electron';
import type {PopupApi} from './menu-config';
const api:PopupApi={state:()=>ipcRenderer.invoke('popup:state'),choose:id=>ipcRenderer.send('popup:choose',id),close:()=>ipcRenderer.send('popup:close')};
contextBridge.exposeInMainWorld('popup',api);
