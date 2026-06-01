/**
 * Utility helper functions
 */

export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function truncateText(text: string, maxLength: number = 120): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

export function parseTagString(tagString: string): string[] {
  return tagString
    .split(',')
    .map(tag => tag.trim())
    .filter(Boolean)
}

export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>
  return (...args: Parameters<T>) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}