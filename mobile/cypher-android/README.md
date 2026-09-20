# Cypher Android

Aplicativo Android independente do Cypher Desktop, desenvolvido com Ionic Vue e Capacitor. O projeto Gradle está em `android/`; o código Vue e o catálogo de módulos estão em `src/`.

## Pré-requisitos

- Node.js compatível com a versão declarada em `package.json` e pnpm.
- Android Studio com Android SDK e Platform Tools instalados.
- Um aparelho Android com **Opções do desenvolvedor** e **Depuração USB** ativadas.

No primeiro uso do aparelho, conecte-o por USB, aceite a chave de depuração exibida nele e confirme que foi reconhecido:

```powershell
adb devices
```

## Desenvolvimento no navegador

```powershell
pnpm install
pnpm dev
```

Abra a URL indicada pelo Vite. Esse modo é útil para desenvolvimento rápido, mas não exercita plugins nativos, biometria, SQLite nativo ou o comportamento do WebView Android.

## Desenvolvimento no aparelho com live reload

O live reload atualiza Vue, CSS e JavaScript no aparelho conectado. Ele não recria código Java/Kotlin, Gradle nem plugins nativos.

### USB, sem depender de Wi-Fi

Com Docker em execução, conecte um único aparelho com a Depuração USB autorizada e execute:

```powershell
pnpm android:usb
```

O comando inicia o backend e o Vite Android no Docker, aplica `adb reverse` da porta `5173` do celular para a porta `5174` do computador e redireciona a API pela porta `8000`. Depois abre o app pelo Capacitor com live reload. Salve os arquivos em `src/` para atualizar o WebView. Use `Ctrl+C` para encerrar o live reload; os serviços Docker permanecem ativos para a próxima execução. Se o Vite Docker não subir, o comando mostra os logs antes de tentar abrir o app.

1. Conecte o aparelho via USB e execute `adb devices`.
2. Garanta que computador e aparelho estejam na mesma rede Wi-Fi.
3. Descubra o IPv4 local do computador com `ipconfig`.
4. Crie `./.env.local` — esse arquivo é local e não deve ser versionado:

```env
VITE_API_URL=http://192.168.X.X:8000/api
```

Substitua `192.168.X.X` pelo IPv4 do computador. No aparelho, `127.0.0.1` aponta para o próprio aparelho, e não para o backend do computador.

Em um terminal, inicie o Vite acessível pela rede:

```powershell
pnpm dev -- --host 0.0.0.0
```

Em outro terminal, instale e execute a build de desenvolvimento no aparelho com live reload:

```powershell
pnpm exec cap run android --live-reload --port 5173
```

Deixe os dois terminais abertos. Ao salvar uma alteração em `src/`, o WebView do aparelho será atualizado. Caso o Windows bloqueie a conexão, permita o Node.js na rede privada no Firewall.

Para uma alteração nativa — `capacitor.config.ts`, dependências Capacitor, permissões Android ou arquivos em `android/` — interrompa o live reload e execute:

```powershell
pnpm android:sync
pnpm exec cap run android
```

O VS Code serve como editor e terminal desse fluxo. Android Studio continua sendo necessário para SDK, ADB, Gradle e inspeção nativa; abra o projeto com `pnpm android:open` quando precisar dele.

## Gerar APK de teste

```powershell
pnpm android:sync
Set-Location android
.\gradlew.bat assembleDebug
```

O APK é gerado em `android/app/build/outputs/apk/debug/app-debug.apk`. Ele usa assinatura de debug e pode ser instalado diretamente no aparelho.

## Edições modulares

As áreas do produto são declaradas em `src/modules/catalog.json`. Cada módulo registra rota, tela, item de navegação, descrição e dependências. As edições selecionam módulos de entrada em `editions/*.json`; dependências são incluídas automaticamente.

```powershell
pnpm build:complete
pnpm build:personal
pnpm build:essentials
pnpm build:saas
```

Para sincronizar uma edição com Android, execute `pnpm android:personal`, `pnpm android:essentials` ou `pnpm android:saas`, e então rode `assembleDebug` em `android/`.
