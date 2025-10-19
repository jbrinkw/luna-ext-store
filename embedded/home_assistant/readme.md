# Home Assistant Extension

Control and monitor your Home Assistant smart home devices through natural language commands.

## Features

- **Device Listing**: Get all available devices with their current states
- **Entity Status**: Check the state and attributes of specific entities
- **Device Control**: Turn lights, switches, fans, and media players on/off
- **TV Remote**: Send commands and launch apps on your TV via Home Assistant remote integration
- **Friendly Name Resolution**: Use natural names like "Living Room Light" instead of entity IDs

## Tools

### HA_GET_devices
List all available Home Assistant devices in supported domains (light, switch, fan, media_player).

**Example**: "list my home devices"

### HA_GET_entity_status
Get the current status and attributes of a specific entity.

**Example**: "what's the status of the living room light?"

**Parameters**:
- `entity_id` or `friendly_name` or `entity_name`: The entity to query

### HA_ACTION_turn_entity_on
Turn on a light, switch, fan, or media player.

**Example**: "turn on the kitchen light"

**Parameters**:
- `entity_id` or `friendly_name` or `entity_name`: The entity to turn on

### HA_ACTION_turn_entity_off
Turn off a light, switch, fan, or media player.

**Example**: "turn off the kitchen light"

**Parameters**:
- `entity_id` or `friendly_name` or `entity_name`: The entity to turn off

### HA_ACTION_tv_remote
Send remote commands or launch apps on your TV.

**Examples**:
- "open spotify on my tv"
- "press home"
- "play"
- "volume up"

**Parameters**:
- `button`: Command or app name (home, play, pause, up, down, spotify, netflix, youtube, etc.)

## Configuration

### Required Environment Variables

```
HA_URL=http://192.168.0.216:8123
HA_TOKEN=your-long-lived-access-token
```

### Optional Environment Variables

```
HA_REMOTE_ENTITY_ID=remote.living_room_tv  # Default TV remote entity
```

## Supported Domains

- **light**: Light bulbs and fixtures
- **switch**: Smart switches and outlets
- **fan**: Fans (including those exposed as switches)
- **media_player**: TVs, speakers, and media devices

## TV Remote Commands

### Navigation
- `up`, `down`, `left`, `right`
- `ok`, `enter`, `select`, `center`
- `back`, `home`

### Playback
- `play`, `pause`, `play/pause`
- `stop`, `next`, `previous`, `rewind`, `fast forward`

### Volume
- `mute`, `volume up`, `volume down`

### Apps (Auto-mapped)
- `youtube` → https://www.youtube.com
- `netflix` → com.netflix.ninja
- `spotify` → com.spotify.tv.android
- `disney` or `disney+` → com.disney.disneyplus

You can also use:
- `open <app>` syntax: "open netflix", "open youtube"
- Raw activity strings: "https://www.youtube.com"
- Raw command codes: "DPAD_UP", "MEDIA_PLAY_PAUSE"

## Dependencies

- `requests`
- `pydantic`
- `python-dotenv`

Install via: `pip install requests pydantic python-dotenv`

## Notes

- The extension automatically resolves friendly names to entity IDs
- If multiple entities match a name, the tool will report the ambiguity
- TV remote requires the Home Assistant Android TV Remote integration

