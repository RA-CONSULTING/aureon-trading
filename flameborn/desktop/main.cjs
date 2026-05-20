const path = require('node:path');
const { app, BrowserWindow, dialog, ipcMain, shell } = require('electron');
const { RuntimeManager, WEB_URL, RUNTIME_URL } = require('./runtime-manager.cjs');

const runtimeManager = new RuntimeManager();
let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1500,
    height: 960,
    minWidth: 1100,
    minHeight: 720,
    title: 'FlameBorn Academy Desktop',
    backgroundColor: '#05080d',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.loadURL(WEB_URL);

  if (process.env.FLAMEBORN_DESKTOP_DEVTOOLS === 'true') {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }
}

ipcMain.handle('flameborn:get-status', async () => {
  return runtimeManager.getStatus();
});

ipcMain.handle('flameborn:restart-service', async (_event, name) => {
  return runtimeManager.restartService(name);
});

ipcMain.handle('flameborn:open-path', async (_event, targetPath) => {
  if (!targetPath || typeof targetPath !== 'string') return false;
  const result = await shell.openPath(targetPath);
  return result === '';
});

ipcMain.handle('flameborn:open-external', async (_event, url) => {
  if (!url || typeof url !== 'string') return false;
  await shell.openExternal(url);
  return true;
});

app.whenReady().then(async () => {
  const status = await runtimeManager.ensureServices();
  const webReachable = Boolean(status.services?.web?.reachable);
  const runtimeReachable = Boolean(status.services?.runtime?.reachable);
  if (!webReachable || !runtimeReachable) {
    await dialog.showErrorBox(
      'FlameBorn startup error',
      [
        `Web UI reachable: ${webReachable}`,
        `Runtime reachable: ${runtimeReachable}`,
        `Expected web: ${WEB_URL}`,
        `Expected runtime: ${RUNTIME_URL}`,
        '',
        'Check logs in logs/desktop/ and start services manually if needed.',
      ].join('\n')
    );
  }
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  runtimeManager.shutdown();
});
