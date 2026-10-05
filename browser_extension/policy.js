export function allowedChatGPT(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' && !parsed.username && !parsed.password &&
      (!parsed.port || parsed.port === '443') &&
      ['chatgpt.com', 'chat.openai.com'].includes(parsed.hostname);
  } catch { return false; }
}
