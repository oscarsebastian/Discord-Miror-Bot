# Discord Mirror Bot

Replica mensajes de un canal de Discord en otro canal mediante un webhook. Esta versión separa configuración, acceso HTTP, transformación de mensajes, persistencia y ejecución en componentes independientes.

## Qué replica

- Texto y hasta 10 embeds por mensaje.
- Títulos, descripciones, colores, enlaces, autores, footers, fields, imágenes y thumbnails.
- Texto y embeds presentes en el mismo mensaje, sin descartar ninguno.
- Enlaces a archivos adjuntos y stickers.
- Nickname del servidor, nombre global, username y avatar del autor.
- Alias estables (`user1`, `user2`, etc.) cuando se activa el modo incógnito.

Las menciones se desactivan en el destino para evitar volver a notificar a usuarios, roles o `@everyone`.

## Requisitos

- Python 3.9 o superior.
- Un bot de Discord con acceso al canal de origen y permiso **Read Message History**.
- Un webhook en el canal de destino.

No uses el token de una cuenta personal. Los self-bots infringen las condiciones de Discord. Utiliza un bot creado desde el portal oficial de desarrolladores.

## Instalación

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita `.env`:

```dotenv
DISCORD_TOKEN=el_token_del_bot
SOURCE_CHANNEL_ID=123456789012345678
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

POLL_INTERVAL_SECONDS=5
INCOGNITO_MODE=false
FETCH_LIMIT=50
```

El archivo `.env` está ignorado por Git. No subas tokens ni webhooks al repositorio.

Inicia el servicio con cualquiera de estas dos formas:

```powershell
python main.py
python -m mirror_bot
```

En la primera ejecución se procesan los últimos `FETCH_LIMIT` mensajes. Después se guarda por cada trabajo el último ID enviado en `data/state.json`. El cursor solo avanza cuando el webhook confirma la entrega, así que un fallo temporal no hace perder mensajes.

## Varias réplicas

Copia `jobs.example.json` como `jobs.json`. Ese archivo solo guarda opciones y los nombres de las variables que contienen secretos; los valores secretos siguen en `.env`.

```dotenv
MIRROR_JOBS_FILE=jobs.json
DISCORD_TOKEN=token_compartido
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
ALERTS_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

Cada trabajo mantiene un cursor independiente, incluso si dos trabajos leen el mismo canal.

## Estructura

```text
main.py                         Punto de entrada compatible
mirror_bot/domain/              Modelos inmutables, sin HTTP ni archivos
mirror_bot/application/         Caso de uso, puertos y creación del payload
mirror_bot/adapters/discord/    Entrada Discord y salida webhook
mirror_bot/adapters/persistence Estado JSON atómico y thread-safe
mirror_bot/adapters/http.py     Reintentos y rate limits compartidos
mirror_bot/runtime.py           Polling, threads y apagado limpio
mirror_bot/config.py            Lectura y validación de .env/jobs.json
mirror_bot/properties.py        URLs base, endpoints y propiedades HTTP de Discord
mirror_bot/app.py               Composition root
tests/                          Pruebas unitarias
```

## Decisiones de diseño

```text
Discord JSON -> DiscordSourceAdapter -> Message
                                        |
                                  MirrorService
                                        |
Discord API  <- DiscordWebhookAdapter <- WebhookPayload

                 MirrorState port
                        ^
                        |
                JsonStateAdapter
```

- Los diccionarios de la API solo existen dentro del adaptador de Discord. `DiscordMessageMapper` los convierte inmediatamente en dataclasses inmutables.
- `application/ports.py` define `MessageSource`, `MessageDestination` y `MirrorState`. El caso de uso no conoce Requests, Discord ni JSON.
- `MirrorService` procesa un lote; `PollingRunner` decide cuándo repetirlo. Separar estas responsabilidades permite probar la lógica sin sleeps ni threads.
- `WebhookPayloadBuilder` es una transformación pura entre modelos y aplica los límites de Discord sin acceder a archivos ni realizar peticiones.
- Los adaptadores de Discord y webhook tienen contratos y errores independientes. `adapters/http.py` comparte solamente el transporte y los reintentos.
- `JsonStateAdapter` es el único componente que escribe estado y lo hace mediante reemplazo atómico protegido entre threads.
- `app.py` es el composition root: es el único lugar que elige qué implementación conecta a cada puerto.
- Los secretos no aparecen en el `repr` de la configuración ni se guardan en los archivos de trabajos.
- `properties.py` centraliza las URLs estructurales y las expone mediante funciones con nombres explícitos. Las URLs concretas de webhooks y los tokens siguen en `.env` porque son secretos de despliegue.

## Pruebas

```powershell
python -m pip install -r requirements-dev.txt
python -m coverage run -m unittest discover
python -m coverage report
```

La cobertura incluye ramas y debe permanecer por encima del 90%. La misma suite se ejecuta automáticamente en GitHub Actions con Python 3.9, 3.11 y 3.13.

## Nota

Respeta las condiciones de Discord, los permisos de los servidores y la privacidad de sus miembros. Este proyecto no evita controles de acceso: el bot solo puede leer canales para los que tenga permisos explícitos.
