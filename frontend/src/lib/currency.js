// Currency code -> display symbol, covering Trade Craft's target markets
// (US, China, Japan, Korea, Hong Kong, Singapore, India, Europe) plus a few
// other common ones Yahoo returns. Falls back to the currency code itself
// (e.g. "AED") rather than showing a bare number with no unit at all.
const SYMBOLS = {
  USD: '$', INR: '₹', JPY: '¥', KRW: '₩', HKD: 'HK$', SGD: 'S$', CNY: '¥',
  EUR: '€', GBP: '£', AUD: 'A$', CAD: 'C$', CHF: 'CHF ', TWD: 'NT$',
}

export function currencySymbol(code) {
  if (!code) return ''
  return SYMBOLS[code] ?? `${code} `
}
