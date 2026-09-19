import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.cypher.financeiro',
  appName: 'Cypher',
  webDir: 'dist',
  server: { androidScheme: 'https' },
  plugins: {
    CapacitorSQLite: { androidIsEncryption: true },
  },
}

export default config
