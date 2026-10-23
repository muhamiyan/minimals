export const passwordRules = [
  { key: 'uppercase', label: 'auth.passwordRules.uppercase' },
  { key: 'lowercase', label: 'auth.passwordRules.lowercase' },
  { key: 'digit', label: 'auth.passwordRules.digit' },
  { key: 'special', label: 'auth.passwordRules.special' },
  { key: 'length', label: 'auth.passwordRules.length' },
] as const

export function checkPassword(password: string) {
  return {
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    digit: /[0-9]/.test(password),
    special: /[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password),
    length: password.length >= 8,
  }
}

export function isPasswordValid(password: string): boolean {
  const checks = checkPassword(password)
  return Object.values(checks).every(Boolean)
}
