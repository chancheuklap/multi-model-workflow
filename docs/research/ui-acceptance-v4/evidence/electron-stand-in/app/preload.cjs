const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('bridge', { save: () => ipcRenderer.invoke('save') });
