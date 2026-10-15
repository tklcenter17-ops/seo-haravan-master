#!/usr/bin/env node
/**
 * Đồng bộ giao diện Apps Script -> bản Vercel (vercel_frontend/).
 *
 *   Script.html  (bọc <script>...</script>)  ->  vercel_frontend/script.js
 *   Style.html   (bọc <style>...</style>)    ->  vercel_frontend/style.css
 *
 * Nguồn chuẩn là bản Apps Script (Script.html / Style.html). Chỉ sửa ở đó,
 * rồi chạy script này; KHÔNG sửa tay script.js / style.css.
 * Index.html KHÔNG được đồng bộ vì bản Vercel có phần riêng (adapter, link CSS, cấu hình VIP).
 *
 * Cách dùng (chạy trong thư mục app_script_admin):
 *   node sync-frontend.js          # ghi đè các file Vercel từ bản Apps Script
 *   node sync-frontend.js --check  # chỉ kiểm tra, thoát mã 1 nếu đang lệch (dùng trước khi push)
 *
 * File này không nằm trong .claspignore whitelist nên sẽ không bị `clasp push` đẩy lên Apps Script.
 */
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const checkOnly = process.argv.includes('--check');

const TARGETS = [
  { src: 'Script.html', dest: 'vercel_frontend/script.js', tag: 'script' },
  { src: 'Style.html', dest: 'vercel_frontend/style.css', tag: 'style' }
];

// Bỏ dòng mở/đóng thẻ bọc ở đầu/cuối file, chuẩn hóa xuống dòng về CRLF (giống các file hiện có).
function unwrap(text, tag, name) {
  const lines = text.replace(/\r\n/g, '\n').split('\n');
  while (lines.length && lines[lines.length - 1].trim() === '') lines.pop();

  const open = new RegExp('^\\s*<' + tag + '(\\s[^>]*)?>\\s*$', 'i');
  const close = new RegExp('^\\s*</' + tag + '>\\s*$', 'i');
  if (!lines.length || !open.test(lines[0])) {
    throw new Error(name + ': dòng đầu không phải <' + tag + '>');
  }
  if (!close.test(lines[lines.length - 1])) {
    throw new Error(name + ': dòng cuối không phải </' + tag + '>');
  }
  return lines.slice(1, -1).join('\r\n') + '\r\n';
}

// So sánh bỏ qua khác biệt dòng trống / khoảng trắng cuối dòng để không báo lệch giả.
function normalize(text) {
  return text
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map((l) => l.replace(/\s+$/, ''))
    .filter((l) => l !== '')
    .join('\n');
}

let outOfSync = 0;

for (const t of TARGETS) {
  const srcPath = path.join(ROOT, t.src);
  const destPath = path.join(ROOT, t.dest);
  const generated = unwrap(fs.readFileSync(srcPath, 'utf8'), t.tag, t.src);
  const current = fs.existsSync(destPath) ? fs.readFileSync(destPath, 'utf8') : null;
  const same = current !== null && normalize(current) === normalize(generated);

  if (checkOnly) {
    console.log((same ? 'OK    ' : 'LỆCH  ') + t.src + ' -> ' + t.dest);
    if (!same) outOfSync++;
  } else if (same) {
    console.log('Không đổi: ' + t.dest);
  } else {
    fs.writeFileSync(destPath, generated, 'utf8');
    console.log('Đã ghi:    ' + t.dest + ' (' + generated.length + ' ký tự)');
  }
}

if (checkOnly && outOfSync) {
  console.error('\n' + outOfSync + ' file Vercel đang lệch. Chạy: node sync-frontend.js');
  process.exit(1);
}
