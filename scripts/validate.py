# TODO validate the following conditions

"""

stuff that can't be checked in the schema:
- are all player IDs unique?
- are the file names identical to the ID in the yaml?
- does the "represents" (client/alternative for) field contain actual IDs
  of media players that have been defined in another file?
- does the "represents" field NOT contain the ID of the player itself?
- does the "represents" field ONLY contain IDs of players
  which themselves do NOT already represent other players?
- does "audio" always come before "audio_..." and "video" before "video_..."?
  can this be checked with JSON schema?
- all players must have the "extra > discord_application_id" field present

subfolder checks:
- all players in "third-party-clients"
  - must have "service: false"
  - must have the "represents" field
- all players in "video-sharing"
  - must have "service: true"
  - must have "video" in "content"
- all players in "podcast-service"
  - must have "service: true"
  - must have "audio_podcast" in "content"
- all players in "offline-players"
  - must have "service: false"
- all players in "music-streaming"
  - must have "service: true"
  - must have "pure: true"
- all players in "multimedia-players"
  - must have "service: false"
  - must have "pure: false"

"""
