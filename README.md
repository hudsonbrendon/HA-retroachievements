# RetroAchievements for Home Assistant

This integration allows you to monitor your RetroAchievements stats and progress in Home Assistant.

## Installation

### HACS (Recommended)
1. Make sure you have [HACS](https://hacs.xyz/) installed.
2. Go to HACS > Integrations > Click the three dots in the top right > Custom repositories.
3. Add this repository URL with category "Integration".
4. Click "Install" on the RetroAchievements integration.
5. Restart Home Assistant.

### Manual Installation
1. Copy the `custom_components/retroarchievements` folder to your Home Assistant's `custom_components` folder.
2. Restart Home Assistant.

## Setup

1. Go to Settings > Devices & Services > Add Integration
2. Search for "RetroAchievements"
3. Enter your RetroAchievements username and API key

## API Key
You can find your RetroAchievements API key in your account settings on the [RetroAchievements website](https://retroachievements.org/).

## Entities

Currently, the integration provides:
- A sensor with your RetroAchievements points and profile data

## Features
- View your RetroAchievements stats in Home Assistant
- Track your progress and achievements

## Roadmap
- Add game-specific tracking
- Track recently unlocked achievements
- Add Lovelace card for displaying achievements

## Troubleshooting

If you encounter issues, please:
1. Enable debug logging for the component in your `configuration.yaml`:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.retroarchievements: debug
   ```
2. Check the logs for error messages
3. Open an issue on GitHub with the logs and steps to reproduce

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
