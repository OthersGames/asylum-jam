"""
This defines a the Server's generic session object. This object represents
a connection to the outside world but don't know any details about how the
connection actually happens (so it's the same for telnet, web, ssh etc).

It is stored on the Server side (as opposed to protocol-specific sessions which
are stored on the Portal side)
"""

import time
from datetime import datetime
from django.conf import settings
from src.scripts.models import ScriptDB
from src.comms.models import Channel
from src.utils import logger, utils
from src.commands import cmdhandler, cmdsethandler
from src.server.session import Session

IDLE_COMMAND = settings.IDLE_COMMAND
_GA = object.__getattribute__
_ObjectDB = None

# load optional out-of-band function module
OOB_FUNC_MODULE = settings.OOB_FUNC_MODULE
if OOB_FUNC_MODULE:
    OOB_FUNC_MODULE = utils.mod_import(settings.OOB_FUNC_MODULE)

# i18n
from django.utils.translation import ugettext as _


#------------------------------------------------------------
# Server Session
#------------------------------------------------------------

class ServerSession(Session):
    """
    This class represents a player's session and is a template for
    individual protocols to communicate with Evennia.

    Each player gets a session assigned to them whenever they connect
    to the game server. All communication between game and player goes
    through their session.

    """
    def __init__(self):
        "Initiate to avoid AttributeErrors down the line"
        self.puppet = None

    def at_sync(self):
        """
        This is called whenever a session has been resynced with the portal.
        At this point all relevant attributes have already been set and self.player
        been assigned (if applicable).

        Since this is often called after a server restart we need to set up
        the session as it was.
        """
        global _ObjectDB
        if not _ObjectDB:
            from src.objects.models import ObjectDB as _ObjectDB

        if not self.logged_in:
            # assign the unloggedin-command set.
            self.cmdset = cmdsethandler.CmdSetHandler(self)
            self.cmdset_storage = [settings.CMDSET_UNLOGGEDIN]
            self.cmdset.update(init_mode=True)
        elif self.puid:
            # reconnect puppet (puid is only set if we are coming back from a server reload)
            obj = _ObjectDB.objects.get(id=self.puid)
            self.player.puppet_object(self.sessid, obj, normal_mode=False)

    def at_login(self, player):
        """
        Hook called by sessionhandler when the session becomes authenticated.

        player - the player associated with the session
        """
        self.player = player
        self.user = player.user
        self.uid = self.user.id
        self.uname = self.user.username
        self.logged_in = True
        self.conn_time = time.time()
        self.puid = None
        self.puppet = None

        # Update account's last login time.
        self.user.last_login = datetime.now()
        self.user.save()

    def at_disconnect(self):
        """
        Hook called by sessionhandler when disconnecting this session.
        """
        if self.logged_in:
            sessid = self.sessid
            player = self.player
            _GA(player.dbobj, "unpuppet_object")(sessid)
            uaccount = _GA(player.dbobj, "user")
            uaccount.last_login = datetime.now()
            uaccount.save()
            # calling player hook
            _GA(player.typeclass, "at_disconnect")()
            self.logged_in = False
            if not self.sessionhandler.sessions_from_player(player):
                # no more sessions connected to this player
                player.is_connected = False

    def get_player(self):
        """
        Get the player associated with this session
        """
        return self.logged_in and self.player

    def get_puppet(self):
        """
        Returns the in-game character associated with this session.
        This returns the typeclass of the object.
        """
        return self.logged_in and self.puppet
    get_character = get_puppet

    def log(self, message, channel=True):
        """
        Emits session info to the appropriate outputs and info channels.
        """
        if channel:
            try:
                cchan = settings.CHANNEL_CONNECTINFO
                cchan = Channel.objects.get_channel(cchan[0])
                cchan.msg("[%s]: %s" % (cchan.key, message))
            except Exception:
                pass
        logger.log_infomsg(message)

    def update_session_counters(self, idle=False):
        """
        Hit this when the user enters a command in order to update idle timers
        and command counters.
        """
        # Store the timestamp of the user's last command.
        self.cmd_last = time.time()
        if not idle:
            # Increment the user's command counter.
            self.cmd_total += 1
            # Player-visible idle time, not used in idle timeout calcs.
            self.cmd_last_visible = time.time()

    def data_in(self, command_string):
        """
        Send Player->Evennia. This will in effect
        execute a command string on the server.
        Eventual extra data moves through oob_data_in
        """
        # handle the 'idle' command
        if str(command_string).strip() == IDLE_COMMAND:
            self.update_session_counters(idle=True)
            return
        if self.logged_in:
            # the inmsg handler will relay to the right place
            self.player.inmsg(command_string, self)
        else:
            # we are not logged in. Execute cmd with the the session directly
            # (it uses the settings.UNLOGGEDIN cmdset)
            cmdhandler.cmdhandler(self, command_string, sessid=self.sessid)
        self.update_session_counters()
    execute_cmd = data_in # alias

    def data_out(self, msg, data=None):
        """
        Send Evennia -> Player
        """
        self.sessionhandler.data_out(self, msg, data)

    def oob_data_in(self, data):
        """
        This receives out-of-band data from the Portal.

        OBS - preliminary. OOB not yet functional in Evennia. Don't use.

        This method parses the data input (a dict) and uses
        it to launch correct methods from those plugged into
        the system.

        data = {oobkey: (funcname, (args), {kwargs}),
                oobkey: (funcname, (args), {kwargs}), ...}

        example:
           data = {"get_hp": ("oob_get_hp, [], {}),
                   "update_counter", ("counter", ["counter1"], {"now":True}) }

        All function names must be defined in settings.OOB_FUNC_MODULE. Each
        function will be called with the oobkey and a back-reference to this session
        as their first two arguments.
        """

        outdata = {}

        for oobkey, functuple in data.items():
            # loop through the data, calling available functions.
            func = OOB_FUNC_MODULE.__dict__.get(functuple[0])
            if func:
                try:
                    outdata[functuple[0]] = func(oobkey, self, *functuple[1], **functuple[2])
                except Exception:
                    logger.log_trace()
            else:
                logger.log_errmsg("oob_data_in error: funcname '%s' not found in OOB_FUNC_MODULE." % functuple[0])
        if outdata:
            # we have a direct result - send it back right away
            self.oob_data_out(outdata)


    def oob_data_out(self, data):
        """
        This sends data from Server to the Portal across the AMP connection.

        OBS - preliminary. OOB not yet functional in Evennia. Don't use.

        data = {oobkey: (funcname, (args), {kwargs}),
                oobkey: (funcname, (args), {kwargs}), ...}

        """
        self.sessionhandler.oob_data_out(self, data)


    def __eq__(self, other):
        return self.address == other.address


    def __str__(self):
        """
        String representation of the user session class. We use
        this a lot in the server logs.
        """
        symbol = ""
        if self.logged_in and hasattr(self, "player") and self.player:
            symbol = "(#%s)" % self.player.id
        try:
            if hasattr(self.address, '__iter__'):
                address = ":".join([str(part) for part in self.address])
            else:
                address = self.address
        except Exception:
            address = self.address
        return "%s%s@%s" % (self.uname, symbol, address)

    def __unicode__(self):
        """
        Unicode representation
        """
        return u"%s" % str(self)

    # easy-access functions

    #def login(self, player):
    #    "alias for at_login"
    #    self.session_login(player)
    #def disconnect(self):
    #    "alias for session_disconnect"
    #    self.session_disconnect()
    def msg(self, string='', data=None):
        "alias for at_data_out"
        self.data_out(string, data=data)


    # Dummy API hooks for use during non-loggedin operation

    def at_cmdset_get(self):
        "dummy hook all objects with cmdsets need to have"
        pass

    # Mock db/ndb properties for allowing easy storage on the session
    # (note that no databse is involved at all here. session.db.attr =
    # value just saves a normal property in memory, just like ndb).

    #@property
    def ndb_get(self):
        """
        A non-persistent store (ndb: NonDataBase). Everything stored
        to this is guaranteed to be cleared when a server is shutdown.
        Syntax is same as for the _get_db_holder() method and
        property, e.g. obj.ndb.attr = value etc.
        """
        try:
            return self._ndb_holder
        except AttributeError:
            class NdbHolder(object):
                "Holder for storing non-persistent attributes."
                def all(self):
                    return [val for val in self.__dict__.keys()
                            if not val.startswith['_']]
                def __getattribute__(self, key):
                    # return None if no matching attribute was found.
                    try:
                        return object.__getattribute__(self, key)
                    except AttributeError:
                        return None
            self._ndb_holder = NdbHolder()
            return self._ndb_holder
    #@ndb.setter
    def ndb_set(self, value):
        "Stop accidentally replacing the db object"
        string = "Cannot assign directly to ndb object! "
        string = "Use ndb.attr=value instead."
        raise Exception(string)
    #@ndb.deleter
    def ndb_del(self):
        "Stop accidental deletion."
        raise Exception("Cannot delete the ndb object!")
    ndb = property(ndb_get, ndb_set, ndb_del)
    db = property(ndb_get, ndb_set, ndb_del)

    # Mock access method for the session (there is no lock info
    # at this stage, so we just present a uniform API)
    def access(self, *args, **kwargs):
        "Dummy method."
        return True
