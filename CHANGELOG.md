# Changelog

## v4

- Renamed `source.win_winrt` to `source.win_smtc` and `source.mac_mediaremote` to `source.mac_bundle`
- Removed `experimental.lin_mpris_identity`. Full Linux MPRIS matcher definitions are now under `source.lin_mpris`
- Added Windows SMTC matcher object for `source.win_smtc` that contains an `app_user_model_id` key for matching the Application User Model ID as usual and an additional `product_name` key to match against the "ProductName" field of the version information of the application's executable or module, in case the Application User Model ID alone is not sufficient to uniquely identify the application in question
- Added Mac Bundle matcher object for `source.mac_bundle` that contains a `bundle_id` key for matching the bundle identifier of an app
- Added Linux MPRIS matcher object for `source.lin_mpris` that contains a `service` key for matching the D-Bus service name as usual and an additional `identity` key to match against the "org.mpris.MediaPlayer2.Identity" D-Bus property, in case the service name alone is not sufficient to uniquely identify the application in question
- Added Web domain matcher object for `source.web_domain` that contains a `domain` key for matching the fully-qualified fully-qualified domain name without any \"www\" subdomain of the website in question
- Added the `caveat` key to the root object and `caveat` and `caveats` to every source matcher object. Caveats are issues that certain implementations of the source application have. Each caveat must be defined and described in the root-level key and must then be mentioned in at least one matcher object of a source application. Caveats can be used by users of players.json to determine whether certain fixes or extra logic must be applied to the application instance that is running on a system

## Previous versions

See git history.
