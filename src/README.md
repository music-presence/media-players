# Definitions

## extra/applescript

This directory contains information on accessing media metadata
from applications that provide a scripting interface on macOS.
The individual yaml files define property access "paths"
that should be walked to get to a specific media attribute
of the currently playing media of the application.

Here is an example definition for Apple Music
that descripes a path of properties to walk:

```objc
artwork_image: [pTrk, cArt, 0, pPCT]
```

How to use this in Objective-C:

```objc
#import <ScriptingBridge/ScriptingBridge.h>

id appleMusic = SBApplication applicationWithBundleIdentifier:@"com.apple.Music"];
id artwork = [[[[[appleMusic propertyWithCode:'pTrk']
    elementArrayWithCode:'cArt'] objectAtIndex:0]
    propertyWithCode:'pPCT'] get];
auto dimensions = [[[artwork representations] objectAtIndex:0] size];
NSLog(@"%fx%f", dimensions.width, dimensions.height); // 800x800
NSLog(@"%@", [artwork class]); // NSImage
```

Note how `pTrk` is read first, then `cArt`,
the number after `cArt` designates that `cArt` is an element array,
then we retrieve the first element at index `0`
and we read the last property `pPCT`.
At the very end of the chain we call `get` to obtain the stored value.
This returns an `NSImage` object.

For more documentation read [schemas/applescript.schema.json](./schemas/applescript.schema.json).
