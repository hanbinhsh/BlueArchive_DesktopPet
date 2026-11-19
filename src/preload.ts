import { contextBridge, ipcRenderer } from 'electron';
import type { PetApi } from './shared';
const api: PetApi = {
  asset:id=>ipcRenderer.invoke('pet:asset',id),
  onPlayback:cb=>{ipcRenderer.on('pet:playback',(_e,value)=>cb(value));},
  playbackEvent:(token,status,error)=>ipcRenderer.send('pet:playback-event',token,status,error),
  durations:values=>ipcRenderer.send('pet:durations',values),
  activity: id => ipcRenderer.send('pet:activity', id),
  touch: () => ipcRenderer.send('pet:touch'),
  onRoam: cb => { ipcRenderer.on('pet:roam', (_e, direction) => cb(direction)); },
  init: () => ipcRenderer.invoke('pet:init'),
  hit: value => ipcRenderer.send('pet:hit', value),
  drag: active => ipcRenderer.send('pet:drag', active),
  resize: size => ipcRenderer.send('pet:resize', size),
  rotate: (yaw, pitch, roll) => ipcRenderer.send('pet:rotate', yaw, pitch, roll),
  menu: () => ipcRenderer.send('pet:menu'),
  report: error => ipcRenderer.send('pet:error', error),
  onVisibility: cb => { ipcRenderer.on('pet:visibility', (_e, value) => cb(value)); },
  onSettings: cb => { ipcRenderer.on('pet:settings', (_e, value) => cb(value)); },
  onCursor: cb => { ipcRenderer.on('pet:cursor', (_e, value) => cb(value)); },
  onAction: cb => { ipcRenderer.on('pet:action', (_e, value) => cb(value)); }
};
contextBridge.exposeInMainWorld('pet', api);
