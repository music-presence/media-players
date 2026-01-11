# players.json specification

> TODO  
> Not yet complete

This specification describes a file format built on top of JSON
to store various identifiers for media players
and provide useful metadata about these media players,
the purpose of which is to allow anyone to identify a media player application
using the identifier that it uses to advertise what media it is playing.

## Table of contents

<!-- TOC depthfrom:2 updateonsave:true -->

- [Table of contents](#table-of-contents)
- [File format definition and use case](#file-format-definition-and-use-case)
- [Scope](#scope)
- [Media players](#media-players)
- [Identifying media players](#identifying-media-players)
    - [Multiple media player identifiers](#multiple-media-player-identifiers)
    - [Matching media player identifiers](#matching-media-player-identifiers)
    - [Preprocessing of specific identifiers](#preprocessing-of-specific-identifiers)
        - [MPRIS on Linux](#mpris-on-linux)
        - [SMTC on Windows](#smtc-on-windows)
        - [App bundle identifier on Mac](#app-bundle-identifier-on-mac)
        - [Internet domain on the web](#internet-domain-on-the-web)

<!-- /TOC -->

## File format definition and use case

TODO

- Identify media players and provide useful metadata
- Operating system-independent
- Allow for live updates

## Scope

This specification currently only covers media players on the desktop.

Media players on mobile devices may be covered in a future revision.

## Media players

A media player can be any of the following:

- An application on the desktop that plays back media
- A website in the browser that plays back media

A media player can only be identified when it advertises what it is playing
through some available system API or interface,
e.g. SMTC on Windows,
MPRIS on Linux,
MediaRemote on Mac
or AppleScript on Mac
and that API provides a meaningful media player identifier
that uniquely identifies that media player.

## Identifying media players

A meaningful media player identifier is one that is not ambiguous
and contains some kind of reference to the app itself,
its development ID or its stable release identifier,
e.g. `MusicBee.exe`, `com.bandcamp.iosapp`
or `AppleInc.AppleMusicWin_nzyj5cx40ttqa!App`.
Identifiers like `Chrome.exe`,
which may appear when a website is playing media,
do not uniquely identify a media player.

There are several different interfaces/app identifier sources
to detect media players per operating system or context.
These interfaces are identified by a short string of the form
`<context>_<interface>`,
where `<context>` is a 3-letter shorthand
that refers to the operating system or source context
and `<interface>` is the source of the identifier,
which may be an operating system interface, system API
or an identifier type that is specific to the context.

The following interface identifiers must be used:

|Interface identifier|Description|
|-|-|
|`lin_mpris`|MPRIS via D-Bus on Linux|
|`win_smtc`|SMTC on Windows|
|`mac_bundle`|Any app bundle identifier on Mac|
|`web_domain`|An internet domain on the web|

Each of the interfaces that are identified by these identifiers
report media player identifiers,
which can be retrieved from the following sources,
specific to the interface:

|Interface|Media player identifier source|
|-|-|
|`lin_mpris`|The D-Bus service identifier|
|`win_smtc`|The `AppUserModelId` field|
|`mac_bundle`|The app bundle identifier|
|`web_domain`|The FQDN of the website|

In most cases media player identifiers must not be processed in their raw form,
but instead must be sanitized and/or expanded
to be used meaningfully in the context of identifying media players.
The following sections outline the rules that must be kept in mind.

Examples for media player identifiers may be
`MusicBee.exe` for "MusicBee" on Windows
or `com.apple.Music` for "Apple Music" on Mac.

### Multiple media player identifiers

A media player can be identified
by multiple different and unique identifiers through the same interface.
If any one of the media player identifiers is matched
against an identifier reported by a media player identifier source,
then that identifier identifies that media player.

### Matching media player identifiers

Media player identifiers must be matched by case-sensitive string comparison
and must compare fully equal.

### Preprocessing of specific identifiers

Before media player identifiers can be used,
they must be preprocessed and sanitized.

#### MPRIS on Linux

With `lin_mpris` the D-Bus service identifier
is used as the media player identifier.

Only service identifiers under the `org.mpris.MediaPlayer2` namespace
may be used as media player identifiers,
as these are identifiers for media players under MPRIS.
The `org.mpris.MediaPlayer2.` prefix must be stripped away
and only the remaining text must be used as the media player identifier.

E.g. the D-Bus service identifier `org.mpris.MediaPlayer2.strawberry`
would become only `strawberry`.
The string `strawberry` then uniquely identifies the "Strawberry" media player.

Some media players have an instance suffix of the form `.<suffix>`
which must be stripped away
in order to be able to consistently identify a media player,
independent of which instance or copy is being used.

The following table contains a non-exhaustive list
of D-Bus service identifier suffixes
that are known to be used by media players:

|Suffix regex pattern|Description|
|-|-|
|`(\.(i\|I)nstance[-_\d]*)`|Used by many media players and browsers|
|`(\.(p\|P)layer[\d]*)`|Used by Valent|
|`(\.mpris[_aA-fF0-9]+)`|Used by KDE Connect|
|`(\.profile[_aA-fF0-9]+)`|Used by Jellyfin|
|`\.GSConnect(\.[^\.\s]+)`|Used by GSConnect|
|`\.mpd(\.[^\.\s]+)`|Used by mpd|

Only the text that is inside a capture group must be stripped away,
as some of these suffixes contain the media player identifier itself,
like `GSConnect` and `mpd`.

A D-Bus service identifier like `org.mpris.MediaPlayer2.firefox.instance_1_579`
must then become `firefox.instance_1_579`
after stripping the `org.mpris.MediaPlayer2.firefox.` prefix
and finally become `firefox` after stripping the `.instance_1_579` suffix.

It is advisable to maintain a list of patterns inside `players.json`
that can be updated, whenever a previously unknown suffix is discovered.

In some cases media players cannot be identified
with the D-Bus service identifier alone,
as that identifier is not unique to the media player
and could used by other media players as well.
This is e.g. the case with the "VacuumTube" media player,
which reports under `org.mpris.MediaPlayer2.chromium`,
due to wrapping a website in a browser that is shipped with the application.

For those cases the D-Bus `org.mpris.MediaPlayer2.Identity` property
must be taken into consideration as well, next to the D-Bus service identifier.
A media player can then be uniquely identified
using both the preprocessed D-Bus service identifier
and the value of the `Identity` property of that media player.

Example: "VacuumTube" may report under the
`org.mpris.MediaPlayer2.chromium.instance2451` D-Bus service identifier
with the `org.mpris.MediaPlayer2.Identity` property set to `VacuumTube`.
The media player is then uniquely identified by the identifier pair
`chromium` (preprocessed D-Bus service name) and `VacuumTube` (Identity).

It is important that any one media player that identifies itself
with a preprocessed D-Bus service identifier of `A` and the identity `B`
is prioritized over a media player that is identified
by the preprocessed D-Bus service identifier `A` alone.
"Valent" may e.g. be identified with the service identifier `Valent`,
but the "OuterTune" mobile app
may be identifier by the service identifier `Valent`
and identity `OuterTune` instead.
Only when the identity matches no known identity string
for a service identifier,
then the media player that only mentions the service identifier
may be identified.

#### SMTC on Windows

With `win_smtc` some media player identifiers
might be the full path to the executable,
e.g. `C:\!Portable\MusicBee\MusicBee.exe`.
Whenever an identifier contains a `\` path separator,
the non-empty basename of the path
must be compared against all known media player identifiers,
in addition to the full identifier itself.
In the example that would be `MusicBee.exe`
in addition to `C:\!Portable\MusicBee\MusicBee.exe`.

Note that identifiers of the form `AppleInc.AppleMusicWin_nzyj5cx40ttqa!App`
can have different capitalizations of the text after the `!` symbol:

- `AppleInc.AppleMusicWin_nzyj5cx40ttqa!APP`
- `AppleInc.AppleMusicWin_nzyj5cx40ttqa!App`
- `AppleInc.AppleMusicWin_nzyj5cx40ttqa!app`

Media player identifiers that contain a `!` character
and that have a string of length 1 or longer after it
must be processed by converting that string after the exclamation mark
to uppercase, title case and lowercase
and compare the resulting identifiers as well,
next to the original one.
This makes it sufficient to only list one variant.

The title case variant must be the one that is listed
and then converted to uppercase and lowercase,
as some identifiers may be capitalized in a certain way
that can't be restored from the uppercase or lowercase variant,
e.g. `!Microsoft.ZuneMusic`
in `Microsoft.ZuneMusic_8wekyb3d8bbwe!Microsoft.ZuneMusic`.

#### App bundle identifier on Mac

With `mac_bundle` no preprocessing is required.

#### Internet domain on the web

With `web_domain` the FQDN (fully-qualified domain name)
of the website without the `www` subdomain
must be used as media player identifier.

Given a known website URL, e.g. `https:///www.deezer.com/track/123`,
the media player identifier would be `deezer.com`.
The `www` subdomain is stripped away to avoid amibiguity and redundancy.
