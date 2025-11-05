"""Natural language formatters for Home Assistant tool outputs."""

from typing import Any, Dict, List, Optional


def format_devices_list(devices: List[Dict[str, Any]]) -> str:
    """Format a list of devices into natural language with full details.

    Args:
        devices: List of device dicts with entity_id, domain, state, friendly_name

    Returns:
        Natural language description including all device details
    """
    if not devices:
        return "No devices found in your Home Assistant setup."

    # Group devices by domain
    lights = []
    switches = []
    fans = []
    media_players = []

    for device in devices:
        domain = device.get("domain", "")
        if domain == "light":
            lights.append(device)
        elif domain == "switch":
            switches.append(device)
        elif domain == "fan":
            fans.append(device)
        elif domain == "media_player":
            media_players.append(device)

    # Build natural language output with full details
    output_parts = []

    if lights:
        output_parts.append("\n**Lights:**")
        for light in lights:
            name = light.get("friendly_name", light.get("entity_id", "Unknown"))
            entity_id = light.get("entity_id", "unknown")
            state = light.get("state", "unknown")
            output_parts.append(f"  - {name} ({entity_id}): {state}")

    if switches:
        output_parts.append("\n**Switches:**")
        for switch in switches:
            name = switch.get("friendly_name", switch.get("entity_id", "Unknown"))
            entity_id = switch.get("entity_id", "unknown")
            state = switch.get("state", "unknown")
            output_parts.append(f"  - {name} ({entity_id}): {state}")

    if fans:
        output_parts.append("\n**Fans:**")
        for fan in fans:
            name = fan.get("friendly_name", fan.get("entity_id", "Unknown"))
            entity_id = fan.get("entity_id", "unknown")
            state = fan.get("state", "unknown")
            output_parts.append(f"  - {name} ({entity_id}): {state}")

    if media_players:
        output_parts.append("\n**Media Players:**")
        for player in media_players:
            name = player.get("friendly_name", player.get("entity_id", "Unknown"))
            entity_id = player.get("entity_id", "unknown")
            state = player.get("state", "unknown")
            output_parts.append(f"  - {name} ({entity_id}): {state}")

    # Add summary header
    total = len(devices)
    summary = f"Found {total} device{'s' if total != 1 else ''} in your home:"

    return summary + "\n" + "\n".join(output_parts)


def format_entity_status(
    entity_id: str,
    state: Optional[str],
    attributes: Dict[str, Any],
    friendly_name: Optional[str] = None
) -> str:
    """Format entity status into natural language.

    Args:
        entity_id: The entity ID
        state: Current state (on, off, playing, etc.)
        attributes: Entity attributes dict
        friendly_name: Optional friendly name

    Returns:
        Natural language description of entity status
    """
    name = friendly_name or attributes.get("friendly_name", entity_id)
    domain = entity_id.split(".")[0] if "." in entity_id else "device"

    if not state:
        return f"The {name} ({entity_id}) status is unknown."

    # Domain-specific formatting
    if domain == "light":
        return f"The {name} ({entity_id}) is {state}."

    elif domain == "switch":
        return f"The {name} ({entity_id}) is {state}."

    elif domain == "fan":
        return f"The {name} ({entity_id}) is {state}."

    elif domain == "media_player":
        media_title = attributes.get("media_title")
        media_artist = attributes.get("media_artist")
        volume = attributes.get("volume_level")
        app_name = attributes.get("app_name")

        if state == "playing":
            parts = [f"The {name} ({entity_id}) is playing"]
            if media_title:
                if media_artist:
                    parts.append(f"'{media_title}' by {media_artist}")
                else:
                    parts.append(f"'{media_title}'")
            if app_name:
                parts.append(f"via {app_name}")
            if volume is not None:
                parts.append(f"at {int(volume * 100)}% volume")
            return " ".join(parts) + "."

        elif state in ["paused", "idle"]:
            return f"The {name} ({entity_id}) is {state}."

        elif state == "off":
            return f"The {name} ({entity_id}) is off."

        else:
            return f"The {name} ({entity_id}) is {state}."

    # Default formatting
    return f"The {name} ({entity_id}) is {state}."


def format_action_result(
    entity_id: str,
    action: str,
    success: bool,
    friendly_name: Optional[str] = None,
    error_message: Optional[str] = None
) -> str:
    """Format action result into natural language.

    Args:
        entity_id: The entity ID
        action: The action performed (turn_on, turn_off)
        success: Whether the action succeeded
        friendly_name: Optional friendly name
        error_message: Error message if action failed

    Returns:
        Natural language confirmation or error message
    """
    name = friendly_name or entity_id

    if not success:
        if error_message:
            return error_message
        return f"I couldn't {action.replace('_', ' ')} the {name}."

    if action == "turn_on":
        return f"I've turned on the {name}."
    elif action == "turn_off":
        return f"I've turned off the {name}."
    else:
        return f"I've performed the {action.replace('_', ' ')} action on the {name}."


def format_tv_remote_action(
    button: str,
    remote_entity: str,
    success: bool,
    error_message: Optional[str] = None
) -> str:
    """Format TV remote action into natural language.

    Args:
        button: The button/action that was sent
        remote_entity: The remote entity ID
        success: Whether the action succeeded
        error_message: Error message if action failed

    Returns:
        Natural language confirmation or error message
    """
    if not success:
        if error_message:
            return error_message
        return f"I couldn't send the '{button}' command to your TV."

    # Get friendly name from remote entity
    device_name = "your TV"
    if "." in remote_entity:
        parts = remote_entity.split(".", 1)[1].replace("_", " ").title()
        if parts:
            device_name = parts

    button_lower = button.lower().strip()

    # App launches
    if button_lower.startswith("open ") or button_lower.startswith("launch "):
        app = button_lower.split(" ", 1)[1]
        return f"I've launched {app.title()} on {device_name}."

    # Known apps
    apps = ["youtube", "netflix", "spotify", "disney", "disney+"]
    if button_lower in apps:
        return f"I've launched {button_lower.title()} on {device_name}."

    # Navigation commands
    nav_commands = {
        "up": "moved up",
        "down": "moved down",
        "left": "moved left",
        "right": "moved right",
        "ok": "pressed OK",
        "enter": "pressed Enter",
        "select": "pressed Select",
        "center": "pressed Center",
        "back": "pressed Back",
        "home": "pressed Home"
    }
    if button_lower in nav_commands:
        return f"I've {nav_commands[button_lower]} on {device_name}."

    # Media controls
    media_commands = {
        "play": "started playback",
        "pause": "paused playback",
        "play/pause": "toggled playback",
        "stop": "stopped playback",
        "next": "skipped to the next track",
        "previous": "gone back to the previous track",
        "prev": "gone back to the previous track",
        "rewind": "rewound",
        "fast forward": "fast forwarded",
        "ff": "fast forwarded"
    }
    if button_lower in media_commands:
        return f"I've {media_commands[button_lower]} on {device_name}."

    # Volume controls
    volume_commands = {
        "mute": "muted",
        "volume up": "turned up the volume",
        "vol up": "turned up the volume",
        "volume down": "turned down the volume",
        "vol down": "turned down the volume"
    }
    if button_lower in volume_commands:
        return f"I've {volume_commands[button_lower]} on {device_name}."

    # Default for unknown commands
    return f"I've sent the '{button}' command to {device_name}."
