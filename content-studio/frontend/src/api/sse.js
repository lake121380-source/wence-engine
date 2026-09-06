// Parse complete events across network chunks, including split UTF-8 characters.
export async function consumeGenerationStream(response, onText) {
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let result = null
  function consume(event) {
    let type = 'message'
    const values = []
    for (const line of event.split('\n')) {
      if (line.startsWith('event:')) type = line.slice(6).trim()
      if (line.startsWith('data:')) values.push(line.slice(5).trimStart())
    }
    if (!values.length) return
    const data = JSON.parse(values.join('\n'))
    if (type === 'error') throw new Error(typeof data === 'string' ? data : data.detail || '生成失败')
    if (type === 'done') {
      if (!data || !data.id) throw new Error('生成结果缺少保存记录')
      result = data
    } else if (typeof data === 'string') onText(data)
  }
  try {
    while (true) {
      const { done, value } = await reader.read()
      buffer += done ? decoder.decode() : decoder.decode(value, { stream: true })
      buffer = buffer.replace(/\r\n/g, '\n')
      let separator
      while ((separator = buffer.indexOf('\n\n')) !== -1) {
        consume(buffer.slice(0, separator))
        buffer = buffer.slice(separator + 2)
      }
      if (done) break
    }
    if (!result) throw new Error('生成连接已中断，未收到完整结果，请重试')
    return result
  } finally {
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}
