export const colors = {
  primary: '#1848E0',
  secondary: '#EFECE6',
  neutrals: {
    ink: '#1B1B1F',
    charcoal: '#444655',
    grey: '#747687',
    lightGrey: '#D5D2CA',
    mist: '#EFECE6',
    white: '#FFFFFF',
    warmCream: '#F5F4F0',
  },
} as const

export type ColorKeys = keyof typeof colors
export type NeutralKeys = keyof typeof colors.neutrals
