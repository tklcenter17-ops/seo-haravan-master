const fs = require('fs');
const path = require('path');
const { Client } = require('D:/CV/Anta_new/App_chat_AI/node_modules/ssh2');
const AdmZip = require('D:/CV/Anta_new/App_chat_AI/node_modules/adm-zip');

const appDir = __dirname;
const zipPath = path.join(appDir, 'lamquet_bot_deploy.zip');

const vpsConfig = {
  host: '103.166.185.85',
  port: 22,
  username: 'root',
  password: 'pFj0adV6xCC6dT3E'
};

async function createZip() {
  console.log('1. Đang đóng gói source code bot...');
  const zip = new AdmZip();

  const includeFiles = [
    'bot.py',
    'config.py',
    'db.py',
    'models.py',
    'normalizer.py',
    'parser.py',
    'pricing.py',
    'radar_service.py',
    'repository.py',
    'search.py',
    'requirements.txt',
    '.env'
  ];

  for (const f of includeFiles) {
    const full = path.join(appDir, f);
    if (fs.existsSync(full)) {
      zip.addLocalFile(full);
      console.log(`   + Thêm file: ${f}`);
    }
  }

  // Add handlers directory
  const handlersDir = path.join(appDir, 'handlers');
  if (fs.existsSync(handlersDir)) {
    const hFiles = fs.readdirSync(handlersDir);
    for (const hf of hFiles) {
      if (hf.endsWith('.py')) {
        zip.addLocalFile(path.join(handlersDir, hf), 'handlers');
        console.log(`   + Thêm handler: handlers/${hf}`);
      }
    }
  }

  zip.writeZip(zipPath);
  console.log(`✓ Đã tạo file zip tại: ${zipPath}`);
  return zipPath;
}

function runRemoteCommand(conn, cmd) {
  return new Promise((resolve, reject) => {
    conn.exec(cmd, (err, stream) => {
      if (err) return reject(err);
      let stdout = '';
      let stderr = '';
      stream.on('close', (code) => {
        resolve({ code, stdout, stderr });
      }).on('data', (d) => {
        stdout += d.toString();
        process.stdout.write(d.toString());
      }).stderr.on('data', (d) => {
        stderr += d.toString();
        process.stderr.write(d.toString());
      });
    });
  });
}

function uploadFile(conn, local, remote) {
  return new Promise((resolve, reject) => {
    conn.sftp((err, sftp) => {
      if (err) return reject(err);
      console.log(`📤 Đang upload ${local} lên VPS (${remote})...`);
      sftp.fastPut(local, remote, (uploadErr) => {
        if (uploadErr) reject(uploadErr);
        else resolve();
      });
    });
  });
}

async function main() {
  await createZip();

  console.log('\n2. Đang kết nối SSH vào VPS 103.166.185.85 (user: root)...');
  const conn = new Client();

  await new Promise((resolve, reject) => {
    conn.on('ready', resolve).on('error', reject).connect(vpsConfig);
  });
  console.log('✓ Kết nối SSH thành công!');

  try {
    const remoteZip = '/root/lamquet_bot.zip';
    const remoteDir = '/root/lamquet-bot';

    // Upload
    await uploadFile(conn, zipPath, remoteZip);
    console.log('✓ Upload hoàn tất!');

    // Prepare dir & unzip (note: excludes existing database to avoid overwriting live data on VPS)
    console.log('\n3. Giải nén cập nhật mã nguồn trên VPS...');
    await runRemoteCommand(conn, `mkdir -p ${remoteDir}/data && unzip -o ${remoteZip} -d ${remoteDir}`);

    // Setup Python venv if not exists
    console.log('\n4. Kiểm tra venv...');
    await runRemoteCommand(conn, `if [ ! -d "${remoteDir}/venv" ]; then python3 -m venv ${remoteDir}/venv; fi`);

    // Pip install
    console.log('\n5. Cập nhật thư viện requirements.txt trên VPS...');
    await runRemoteCommand(conn, `${remoteDir}/venv/bin/pip install -r ${remoteDir}/requirements.txt`);

    // PM2 Reload / Restart
    console.log('\n6. Khởi động lại bot trên PM2...');
    await runRemoteCommand(conn, `pm2 restart "lamquet-bot" || (cd ${remoteDir} && pm2 start venv/bin/python --name "lamquet-bot" -- bot.py)`);
    await runRemoteCommand(conn, `pm2 save`);

    // Check logs
    console.log('\n7. Đọc logs mới nhất của bot trên VPS:');
    await runRemoteCommand(conn, `sleep 2 && pm2 logs lamquet-bot --lines 15 --nostream`);

    console.log('\n🎉 CẬP NHẬT BOT LÊN VPS THÀNH CÔNG 100%! KHÔNG CẦN BẬT BROWSER!');
  } finally {
    conn.end();
    if (fs.existsSync(zipPath)) {
      fs.unlinkSync(zipPath);
    }
  }
}

main().catch(err => {
  console.error('\n❌ Deploy thất bại:', err);
  process.exit(1);
});
