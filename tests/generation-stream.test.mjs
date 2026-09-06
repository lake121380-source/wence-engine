import { test } from 'node:test';
import assert from 'node:assert/strict';
import { consumeGenerationStream } from '../content-studio/frontend/src/api/sse.js';

function response(text) {
  const bytes = new TextEncoder().encode(text);
  return new Response(new ReadableStream({ start(controller) {
    for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
    controller.close();
  } }));
}
test('split UTF-8 and event frames preserve generated content and saved record', async () => {
  let text = '';
  const result = await consumeGenerationStream(response('data: "中文内容"\r\n\r\nevent: done\r\ndata: {"id":12}\r\n\r\n'), value => text += value);
  assert.equal(text, '中文内容'); assert.equal(result.id, 12);
});
test('upstream error is surfaced and a truncated stream cannot look successful', async () => {
  await assert.rejects(consumeGenerationStream(response('event: error\ndata: "模型暂不可用"\n\n'), () => {}), /模型暂不可用/);
  await assert.rejects(consumeGenerationStream(response('data: "partial"\n\n'), () => {}), /连接已中断/);
});
