import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';

function loadMessageUtils() {
  const currentDir = path.dirname(fileURLToPath(import.meta.url));
  const sourcePath = path.resolve(currentDir, '..', 'js', 'chat-message-utils.js');
  const source = fs.readFileSync(sourcePath, 'utf8');

  const windowObject = {
    open: () => {},
  };

  const context = vm.createContext({
    window: windowObject,
    URL,
    console,
  });

  vm.runInContext(source, context, { filename: sourcePath });
  return windowObject.FreightChatMessageUtils;
}

function runTest(name, fn) {
  try {
    fn();
    console.log(`PASS ${name}`);
  } catch (error) {
    console.error(`FAIL ${name}`);
    throw error;
  }
}

const messageUtils = loadMessageUtils();

runTest('escapeHtml escapes HTML-sensitive characters', () => {
  assert.equal(
    messageUtils.escapeHtml(`<tag attr="value">'quoted' & test`),
    '&lt;tag attr=&quot;value&quot;&gt;&#39;quoted&#39; &amp; test',
  );
});

runTest('stripInternalSystemData removes internal debug payloads', () => {
  const input = [
    'ก่อนหน้า',
    '[SYSTEM DATA]{"tracking_results":[{"status":"Out for Delivery"}]}',
    '```json',
    '{"tracking_results":[{"details":"secret"}]}',
    '```',
    'ข้อความจริง',
  ].join('\n');

  const sanitized = messageUtils.stripInternalSystemData(input);
  assert.equal(sanitized, 'ก่อนหน้า\n\nข้อความจริง');
});

runTest('sanitizeUrl only allows http and https URLs', () => {
  assert.equal(messageUtils.sanitizeUrl('https://example.com/path?q=1'), 'https://example.com/path?q=1');
  assert.equal(messageUtils.sanitizeUrl('javascript:alert(1)'), '');
});

runTest('extractTrackingLinkData detects porlor links and keeps summary text', () => {
  const details = messageUtils.extractTrackingLinkData(
    'DO 1314640315 ไปกับ Porlor https://aeryadunwit.github.io/Frieght/porlor-tracking.html?track=1314640315',
    { skyfrog: 'https://track.skyfrog.net' },
  );

  assert.ok(details);
  assert.equal(details.isPorlor, true);
  assert.equal(details.isSkyfrog, false);
  assert.match(details.summary, /DO 1314640315/);
});

runTest('renderTrackingCard returns a Skyfrog action card for Skyfrog links', () => {
  const html = messageUtils.renderTrackingCard(
    'ไม่พบข้อมูลในระบบ ลองต่อที่ https://track.skyfrog.net/h1IZM?TrackNo=1314645630',
    { skyfrog: 'https://track.skyfrog.net' },
  );

  assert.ok(html);
  assert.match(html, /Skyfrog/);
  assert.match(html, /1314645630/);
});
