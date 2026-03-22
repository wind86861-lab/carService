/**
 * Format a number string with space thousand separators.
 * "100000" → "100 000"
 */
export function formatWithSpaces(value) {
  if (!value && value !== 0) return ''
  const digits = String(value).replace(/\D/g, '')
  if (!digits) return ''
  return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
}

/**
 * Strip spaces from formatted number string → raw digits.
 * "100 000" → "100000"
 */
export function stripSpaces(value) {
  return String(value).replace(/\s/g, '')
}
