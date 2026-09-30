export const passwordRules = [
  { key: 'uppercase', label: 'One uppercase letter' },
  { key: 'lowercase', label: 'One lowercase letter' },
  { key: 'digit', label: 'One number' },
  { key: 'special', label: 'One special character' },
  { key: 'length', label: 'At least 8 characters' },
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
