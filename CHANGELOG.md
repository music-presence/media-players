# Changelog

## v4

- Renamed `source.win_winrt` to `source.win_smtc` and `source.mac_mediaremote` to `source.mac_bundle`
- Removed `experimental.lin_mpris_identity`. Full Linux MPRIS definitions are now under `source.lin_mpris`
- Added Linux MPRIS matcher object for `source.lin_mpris` that contains a `service` key for matching the D-Bus service name as usual and an `identity` key to match against the "org.mpris.MediaPlayer2.Identity" D-Bus property

## v3 and older

See git history.
