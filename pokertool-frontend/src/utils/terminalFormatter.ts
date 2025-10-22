/**Terminal Output Formatter - ANSI colors, clickable paths, timestamps*/
export const formatTerminalOutput = (text: string): string => {
  const withTimestamp = `[${new Date().toLocaleTimeString()}] ${text}`;
  return withTimestamp.replace(/`([^`]+)`/g, '<span class="path">$1</span>');
};

export const parseANSI = (text: string): string => {
  const colorMap: Record<string, string> = {
    '\x1b[31m': '<span style="color: #ff6b6b">', '\x1b[32m': '<span style="color: #51cf66">',
    '\x1b[33m': '<span style="color: #ffd43b">', '\x1b[0m': '</span>'
  };
  let formatted = text;
  Object.entries(colorMap).forEach(([code, html]) => {
    formatted = formatted.replace(new RegExp(code, 'g'), html);
  });
  return formatted;
};
