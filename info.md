{% if prerelease %}
Please note that this is a beta version which is still undergoing final testing before its official release.

Following documentation may be out-dated or not for beta release

---

請注意，目前版本為 Beta 版，此版本仍在開發或測試中，可能會發生某些未預期的情況或錯誤，且下列文件可能不適用於此版本，請斟酌使用
{% endif %}


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
