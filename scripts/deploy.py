VERSION = 3

# TODO write a players.schema.json for the deployed json file
# TODO deploy everything from source into a monolith players.json file

"""

- must contain a latest field (set to true) which indicates that
  the generated file is the latest version of that file and is uptodate
- perhaps add the timestamp of when the file was last generated
- think about how to integrate logos in the best possible way
  - square version: original logo without any constraints
  - circular version: it should be possible to overlay the logo with a circle
    without cutting away any identifying parts of the logo, so that it can be
    used in a context where a circular logo is expected
  - these logos should not have any thick borders like the old logos,
    instead create an API that can add a border to the logo with custom
    colours, transparency and a custom border thickness
  - TODO copy logos from the internal repository into the src/logos directory
    and modify them according to the new requirements
- make sure parsing v3 doesn't require too much code rewriting from v2
- write a GitHub runner that deploys players on every commit (gh-pages branch)
  - move the old (v1, v2) versions of the players to that branch
- create a pre-commit and/or pre-deploy hook that checks if everything's valid
  by running the validate.py script in this directory
- ...

"""
