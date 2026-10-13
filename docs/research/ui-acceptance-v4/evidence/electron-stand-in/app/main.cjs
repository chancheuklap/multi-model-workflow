const { app, BrowserWindow, ipcMain } = require('electron');
const fs = require('fs'), path = require('path');
ipcMain.handle('save', () => { fs.writeFileSync(path.join(process.env.DATA_DIR, 'job.txt'), 'dubbing'); return '已开始'; });
app.whenReady().then(() => {
  const w = new BrowserWindow({ width: 1000, height: 700, show: false, webPreferences: { preload: path.join(__dirname, 'preload.cjs') } });
  w.loadURL('about:blank');
});
