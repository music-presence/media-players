[![Deploy](https://github.com/music-presence/media-players/actions/workflows/actions.yml/badge.svg)](https://github.com/music-presence/media-players/actions/workflows/actions.yml)

# List of desktop and web media players

This repository contains a list of identifiers
for various media players on the desktop and the web.
These can be used to identify media players
that are playing media on a desktop device
and which report it through the operating system's native media integration,
i.e. SMTC on Windows, MediaRemote on macOS and MPRIS/DBUS on Linux.

This repository was mainly created for use with
[Music Presence](https://musicpresence.app),
but can also be used in other contexts
where uniquely identifying a media player is desirable.

For a visual overview of players in this repository visit
[musicpresence.pocha.moe](https://musicpresence.pocha.moe/)
(thanks [@mercurialworld](https://github.com/mercurialworld)).

## Public API

A public endpoint is maintained at `live.musicpresence.app`
which is a simple GitHub Pages site with static files,
the repository for which can be found here:
https://github.com/music-presence/live.

The current version of this endpoint is `v3`,
available at https://live.musicpresence.app/v3:

|File|Platforms|URL|
|-|-|-|
|`players.json`|All|https://live.musicpresence.app/v3/players.json|
|`players.win.json`|Windows+Web|https://live.musicpresence.app/v3/players.win.json|
|`players.mac.json`|Mac+Web|https://live.musicpresence.app/v3/players.mac.json|
|`players.lin.json`|Linux+Web|https://live.musicpresence.app/v3/players.lin.json|
|`players.web.json`|Web|https://live.musicpresence.app/v3/players.web.json|

The first file contains players for all platforms,
the remaining files contain players for only the specified platforms.

There are also minified versions available for each file, e.g.
[`players.min.json`](https://live.musicpresence.app/v3/players.min.json)

Any other hosted files are indirectly accessible by parsing this JSON file,
this includes JSON Schema files for validation and documentation
as well as icons for the media players that are contained in the file.

Please refer to the linked schema in the root property `$schema`,
[src/schemas/players.schema.json](./src/schemas/players.schema.json) or
https://live.musicpresence.app/v3/schemas/players.schema.json
for documentation on all fields in the players.json file,
including how to check if v3 is still the latest version.

The underlying repository for this endpoint
is used as "append-only" file storage,
that means any file you can access now,
you can also access at any point in the future.
No file is ever removed, but some files may be overwritten or updated,
especially those of the most recent version (v3).
Older versions are generally not kept up-to-date.

## Maintaining and contributing

To maintain or contribute to this repository, keep the following notes in mind:

TODO

### Directory structure

```
/out/public/: public root under live.musicpresence.app/v3/
/out/public/players.json: the root players.json file
/out/public/players.min.json: the root players.json file, minified
/out/public/schemas/: all schemas from /src/schemas, except internal schemas
/out/public/icons/: all icons for media players (image files)
/out/public/icons/<player>/: all icons for a media player identified by <player>
```

---

### License

TODO
