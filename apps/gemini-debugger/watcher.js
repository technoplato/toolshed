const chokidar = require('chokidar');
const fs = require('fs');
const path = require('path');

// Configuration
const WATCH_DIR = '/Users/laptop/.gemini/antigravity';
const CAPTURE_DIR = path.join(__dirname, 'captures');

// Ensure capture directory exists
if (!fs.existsSync(CAPTURE_DIR)) {
  fs.mkdirSync(CAPTURE_DIR, { recursive: true });
}

console.log(`Starting Gemini Debugger...`);
console.log(`Watching: ${WATCH_DIR}`);
console.log(`Capturing to: ${CAPTURE_DIR}`);

// Initialize watcher
// We ignore initial add events to avoid copying thousands of existing files on startup
const watcher = chokidar.watch(WATCH_DIR, {
  ignored: [
    '**/node_modules/**' 
  ],
  persistent: true,
  ignoreInitial: true,
  depth: 5 // Watch subdirectories
});

watcher
  .on('add', (filePath) => handleFileEvent('ADD', filePath))
  .on('change', (filePath) => handleFileEvent('CHANGE', filePath));

function handleFileEvent(type, filePath) {
  const filename = path.basename(filePath);
  const ext = path.extname(filePath);

  // We are interested in .tmp, .pb, and .resolved files
  // Also brain markdown files as they change
  if (['.tmp', '.pb', '.resolved', '.md'].includes(ext) || filename.includes('.resolved')) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const safeFilename = filename.replace(/[^a-zA-Z0-9._-]/g, '_');
    const destPath = path.join(CAPTURE_DIR, `${timestamp}_${type}_${safeFilename}`);

    try {
      // Use copyFile for speed. If file is gone (deleted quickly), it might fail.
      fs.copyFile(filePath, destPath, (err) => {
        if (err) {
          if (err.code === 'ENOENT') {
            // File disappeared before we could copy it - common for .tmp files
            console.log(`[${type}] Missed ephemeral file: ${filename}`);
          } else {
            console.error(`[${type}] Error copying ${filename}:`, err.message);
          }
        } else {
          console.log(`[${type}] Captured: ${filename} -> ${path.basename(destPath)}`);
        }
      });
    } catch (e) {
      console.error(`[${type}] Exception handling ${filename}:`, e.message);
    }
  }
}

console.log('Watcher is ready. Trigger some IDE actions to see captures.');

