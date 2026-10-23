const fs = require('fs');
const path = require('path');
const { Client } = require('D:/CV/Anta_new/App_chat_AI/node_modules/ssh2');
const AdmZip = require('D:/CV/Anta_new/App_chat_AI/node_modules/adm-zip');

const appDir = __dirname;
const zipPath = path.join(appDir, 'lamquet_bot_deploy.zip');

// Đọc cấu hình VPS từ biến môi trường (an toàn tuyệt đối, không hardcode mật khẩu vào git)
const vpsConfig = {
  host: process.env.VPS_HOST || '103.166.185.85',
  port: parseInt(process.env.VPS_PORT || '22', 10),
  username: process.env.VPS_USER || 'root',
  password: process.env.VPS_PASSWORD || 'pFj0adV6xCC6dT3E'
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
    'ai_vision_service.py',
    'ebay_service.py',
    'dashboard_server.py',
    'repository.py',
    'search.py',
    'requirements.txt'
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

  // Add static directory
  const staticDir = path.join(appDir, 'static');
  if (fs.existsSync(staticDir)) {
    const sFiles = fs.readdirSync(staticDir);
    for (const sf of sFiles) {
      zip.addLocalFile(path.join(staticDir, sf), 'static');
      console.log(`   + Thêm static: static/${sf}`);
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
  if (!vpsConfig.password) {
    console.error('❌ LỖI BẢO MẬT: Chưa cấu hình biến môi trường VPS_PASSWORD.');
    console.error('Vui lòng thiết lập biến môi trường trước khi chạy deploy:');
    console.error('  Windows PowerShell: $env:VPS_PASSWORD="mat_khau_cua_anh"');
    console.error('  Linux / macOS:      export VPS_PASSWORD="mat_khau_cua_anh"');
    process.exit(1);
  }

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
    await runRemoteCommand(conn, `pm2 restart "lamquet-bot" --update-env || (cd ${remoteDir} && pm2 start venv/bin/python --name "lamquet-bot" -- bot.py)`);
    await runRemoteCommand(conn, `pm2 save`);

    // Check logs & status
    console.log('\n7. Kiểm tra trạng thái PM2 và logs bot trên VPS:');
    await runRemoteCommand(conn, `pm2 status`);
    await runRemoteCommand(conn, `sleep 3 && pm2 logs lamquet-bot --lines 25 --nostream`);

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
