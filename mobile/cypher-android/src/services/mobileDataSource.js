import { Capacitor } from '@capacitor/core'
import { localApi } from '@/services/localDataSource'
import { initializeMobileDatabase } from '@/services/mobileDatabase'

export async function createDataSource() {
  if (Capacitor.isNativePlatform()) await initializeMobileDatabase()
  return localApi
}
