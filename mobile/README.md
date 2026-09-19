# Cypher Mobile

`cypher-android/` é um projeto Ionic Vue/Capacitor independente do frontend desktop. Ele possui dependências, rotas, catálogo de módulos, configurações Android e builds próprios.

```powershell
cd mobile/cypher-android
pnpm install
pnpm android:sync
cd android
.\gradlew.bat assembleDebug
```

As edições do APK são definidas em `cypher-android/editions/` e o catálogo de módulos está em `cypher-android/src/modules/catalog.json`.
