[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/custom-components/hacs)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/osk2/panasonic_smart_app?style=for-the-badge)
[![GitHub license](https://img.shields.io/github/license/osk2/panasonic_smart_app?style=for-the-badge)](https://github.com/osk2/panasonic_smart_app/blob/master/LICENSE)

# Hitachi Smart App

| ![smart-app-icon](https://raw.githubusercontent.com/n71154plus/Hitachi_smart_app/master/assets/smart-app-icon.png) |

Home Assistant integration for [Hitachi Smart App](https://play.google.com/store/apps/details?id=com.hitachi.TaiSEIA.smarthome).

This integration allows you to control your Hitachi appliances.

# Installation

### Via HACS (recommended)

Search and install `Hitachi Smart App` in HACS

### Manually

Copy `custom_components/Hitachi_smart_app` into your `custom_components/`.

# Configuration

1. Search `Hitachi Smart App` in integration list
2. Follow steps on UI to finish configuration

# Note

### Tested Devices

Following devices were tested.

Feel free to report working device by opening an [issue](https://github.com/n71154plus/Hitachi_smart_app/issues)

| Device Type | Module Type  |
| ----------- | ------------ |
| RAS-22NK    | RC-W02XE     |
| RAS-28NK    | RC-W02XE     |
| RAS-36NK    | RC-W02XE     |
| RAS-40NK    | RC-W02XE     |
| RAS-50NK    | RC-W02XE     |
| RAS-63NK    | RC-W02XE     |
| RAS-71NK    | RC-W02XE     |
| RAS-81NK    | RC-W02XE     |
| RAS-90NK    | RC-W02XE     |
| RD-160HH    | built-in     |
| RD-200HH    | built-in     |
| RD-240HH    | built-in     |
| RD-280HH    | built-in     |
| RD-320HH    | built-in     |
| RD-360HH    | built-in     |


### Available Entities

| Device Type  | Entity Type   | Note                         |
| ------------ | ------------- | ---------------------------- |
| AC           | climate       |                              |
| Dehumidifier | humidifier    |                              |

For missing entities, open an issue or submit a PR 💪

### Enable Logs

Add following configs to `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.Hitachi_smart_app: debug
```

# License

This project is licensed under MIT license. See [LICENSE](LICENSE) file for details.
