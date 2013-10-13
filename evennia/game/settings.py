
######################################################################
# Evennia MU* server configuration file
#
# You may customize your setup by copy&pasting the variables you want
# to change from the master config file src/settings_default.py to
# this file. Try to *only* copy over things you really need to customize
# and do *not* make any changes to src/settings_default.py directly.
# This way you'll always have a sane default to fall back on
# (also, the master config file may change with server updates).
#
######################################################################

from src.settings_default import *

######################################################################
# Custom settings
######################################################################
# This is the name of your game. Make it catchy!
SERVERNAME = "Starship Pythia"

# Base paths for typeclassed object classes. These paths must be
# defined relative evennia's root directory. They will be searched in
# order to find relative typeclass paths.
#OBJECT_TYPECLASS_PATHS = ["game.gamesrc.objects", "game.gamesrc.objects.examples", "contrib"]
#SCRIPT_TYPECLASS_PATHS = ["game.gamesrc.scripts", "game.gamesrc.scripts.examples", "contrib"]
#PLAYER_TYPECLASS_PATHS = ["game.gamesrc.objects", "contrib"]

# Typeclass for player objects (linked to a character) (fallback)
##BASE_PLAYER_TYPECLASS = "game.gamesrc.objects.player"
# Typeclass and base for all objects (fallback)
##BASE_OBJECT_TYPECLASS = "game.gamesrc.objects.objects.Object"
# Typeclass for character objects linked to a player (fallback)
BASE_CHARACTER_TYPECLASS = "game.gamesrc.objects.charB.Character"
# Typeclass for rooms (fallback)
##BASE_ROOM_TYPECLASS = "game.gamesrc.objects.Room"
# Typeclass for Exit objects (fallback).
##BASE_EXIT_TYPECLASS = "game.gamesrc.objects.Exit"
# Typeclass for Scripts (fallback). You usually don't need to change this
# but create custom variations of scripts on a per-case basis instead.
##BASE_SCRIPT_TYPECLASS = "game.gamesrc.scripts.scripts.DoNothing"
# The home location for new characters. This must be a unique
# dbref (default is Limbo #2). If you want more advanced control over
# start locations, copy the "create" command from
# src/commands/default/unloggedin.py and customize.
CHARACTER_DEFAULT_HOME = "#2"

# Default set for logged in player with characters (fallback)
CMDSET_CHARACTER = "game.gamesrc.commands.cmdset.CharacterCmdSet"

######################################################################
# SECRET_KEY was randomly seeded when settings.py was first created.
# Don't share this with anybody. It is used by Evennia to handle
# cryptographic hashing for things like cookies on the web side.
######################################################################
SECRET_KEY = 'Y"*k!Z$8dW_`<gcKPm/=BlU%}0>6RjX,u)+|aHyo'

