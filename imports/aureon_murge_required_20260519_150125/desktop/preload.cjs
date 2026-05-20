const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('flamebornDesktop', {
  getStatus: () => ipcRenderer.invoke('flameborn:get-status'),
  restartService: (name) => ipcRenderer.invoke('flameborn:restart-service', name),
  openPath: (targetPath) => ipcRenderer.invoke('flameborn:open-path', targetPath),
  openExternal: (url) => ipcRenderer.invoke('flameborn:open-external', url),
});
