// styled-components theme type declarations
import 'styled-components'
import { ThemeColors } from './theme'

declare module 'styled-components' {
  export interface DefaultTheme extends ThemeColors {}
}
