# PyA Bot

Bot de Discord para la comunidad: docs de Python, ejercicios de Codewars, moderación con warnings persistentes y consultas a IA.

## Setup

```bash
cd bot
python -m venv .venv
.venv\Scripts\activate     # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

Crea `bot/token.env`:

```env
DISCORD_TOKEN=tu_token_de_discord
DEV_GUILD_ID=1490702264917033141        # opcional: sync inmediato en guild de pruebas
MOD_LOG_CHANNEL_ID=                     # opcional: canal para logs de moderación
MOD_WHITELIST_CHANNELS=                 # opcional: IDs separados por coma
MOD_WHITELIST_ROLES=                    # opcional: IDs separados por coma
ANTHROPIC_API_KEY=                      # opcional: habilita -ask
```

## Ejecutar

```bash
python main.py
```

## Tests

```bash
pip install pytest
pytest bot/tests
```

## Comandos

| Comando | Descripción |
|---|---|
| `-help` | Lista de comandos |
| `-python <lib>` | Docs de librería estándar |
| `-ml <lib>` | Docs de Machine Learning |
| `-api <lib>` | Docs de APIs/backend |
| `-exercise [1-8]` | Kata aleatorio de Codewars |
| `-ask <pregunta>` | Pregunta a la IA (requiere API key) |
| `-anuncio <título> <mensaje>` | Anuncio con `@everyone` (admin) |
| `-kick <user> [razón]` | Expulsar |
| `-ban <user> confirm:SI [razón]` | Ban permanente (requiere confirmación) |
| `-mute <user> <unidad> <cantidad> [razón]` | Timeout temporal |
| `-warn <user> [razón]` | Advertencia (3 = kick automático) |
| `-warnings <user>` | Listar warnings |
| `-clearwarns <user>` | Borrar warnings (admin) |

## Moderación automática

- Spam de frecuencia: 7 mensajes en 6s → mute 5min
- Caracteres repetidos (`aaaaa+`)
- Palabra repetida >3 veces
- Cadenas sin sentido (palabras alfabéticas >15 chars con <15% vocales)
- MAYÚSCULAS alternadas → re-publica en minúsculas
- Invites a otros servidores → eliminadas
- Anti-raid: 5+ joins en 60s → alerta en mod-log

URLs, emojis (custom y unicode), stickers y attachments están exentos del análisis de spam.

## Despliegue

`Procfile` listo para Railway/Render. El módulo `keep_alive` corre `waitress` en `:$PORT` para mantener el servicio activo en el plan gratuito.
