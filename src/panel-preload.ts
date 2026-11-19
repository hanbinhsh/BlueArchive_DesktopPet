import { contextBridge, ipcRenderer } from 'electron';
import type { PanelApi } from './shared';
const api: PanelApi = {
  dirty:value=>ipcRenderer.send('panel:dirty',value),
  state: () => ipcRenderer.invoke('panel:state'),
  command: (command, value) => ipcRenderer.invoke('panel:command', command, value),
  onState: cb => { ipcRenderer.on('panel:state', (_e, state) => cb(state)); }
};
contextBridge.exposeInMainWorld('panel', api);
