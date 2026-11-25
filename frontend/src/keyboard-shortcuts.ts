export const isMac = () => /Mac|iPhone|iPad/.test(navigator.platform);
export function shortcutLabel(shortcut?: string): string {
  if (!shortcut) return '';
  const symbols: Record<string, string> = { Mod: isMac() ? '⌘' : 'Ctrl', Alt: isMac() ? '⌥' : 'Alt',
    Shift: isMac() ? '⇧' : 'Shift', Enter: '↵', ArrowUp: '↑', ArrowDown: '↓', Tab: 'Tab', F10: 'F10' };
  return shortcut.split('-').map(key => symbols[key] ?? key.toUpperCase()).join(isMac() ? '' : '+');
}
export function ariaShortcut(shortcut?: string) {
  return shortcut?.split('-').map(key => key === 'Mod' ? isMac() ? 'Meta' : 'Control' : key).join('+');
}
