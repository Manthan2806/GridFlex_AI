export const colors = {
  primary: '#6B1E2E',
  secondary: '#F1E7D6',
  neutrals: {
    ink: '#171412',
    charcoal: '#302B27',
    grey: '#6F6963',
    lightGrey: '#B9B2AA',
    mist: '#E5E0DA',
    white: '#FFFFFF',
  },
} as const

export type ColorKeys = keyof typeof colors
export type NeutralKeys = keyof typeof colors.neutrals