export function parseReleaseNotes(input = '') {
  const bullets = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => /^[-*]\s+\S/.test(line))
    .map((line) => line.replace(/^[-*]\s+/, '').trim());

  return {
    bullets,
    count: bullets.length
  };
}
