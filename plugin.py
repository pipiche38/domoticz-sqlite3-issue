"""
<plugin key="zzSqlite3" name="ZZ Domoticz SQLITE3 issue" author="pipiche38" version="0.0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://www.google.com/">
    <description>
        <h2> Plugin Zigate for Domoticz </h2><br/>
    <h3> Short description </h3>
           This plugin allow Domoticz to access to the Zigate (Zigbee) worlds of devices.<br/>
    <h3> Configuration </h3>
          You can use the following parameter to interact with the Zigate:<br/>
    <ul style="list-style-type:square">
            <li> Model: Wifi</li>
            <ul style="list-style-type:square">
                <li> IP : For Wifi Zigate, the IP address. </li>
                <li> Port: For Wifi Zigate,  port number. </li>
                </ul>
                <li> Model USB ,  PI or DIN:</li>
            <ul style="list-style-type:square">
                <li> Serial Port: this is the serial port where your USB or DIN Zigate is connected. (The plugin will provide you the list of possible ports)</li>
                </ul>
            <li> Initialize ZiGate with plugin: This is a required step, with a new ZiGate or if you have done an Erase EEPROM. This will for instance create a new ZigBee Network. </li>
    </ul>
    <h3> Support </h3>
    Please use first the Domoticz forums in order to qualify your issue. Select the ZigBee or Zigate topic.
    </description>
    <params>
        <param field="Mode6" label="Verbors and Debuging" width="150px" required="true" default="None">
            <options>
                        <option label="None" value="0"  default="true"/>
                        <option label="Plugin Verbose" value="2"/>
                        <option label="Domoticz Plugin" value="4"/>
                        <option label="Domoticz Devices" value="8"/>
                        <option label="Domoticz Connections" value="16"/>
                        <option label="Verbose+Plugin+Devices" value="14"/>
                        <option label="Verbose+Plugin+Devices+Connections" value="30"/>
                        <option label="Domoticz Framework - All (useless but in case)" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""


import Domoticz
import sqlite3
import time

DB_VERSION = 0x0003

class PersistingListener:
    def __init__(self, database_file):
        self._database_file = database_file
        self._db = sqlite3.connect(database_file, detect_types=sqlite3.PARSE_DECLTYPES)
        self._cursor = self._db.cursor()

        self._enable_foreign_keys()
        self._create_table_devices()
        self._create_table_endpoints()
        self._create_table_clusters()
        self._create_table_node_descriptors()
        self._create_table_output_clusters()
        self._create_table_attributes()
        self._create_table_groups()
        self._create_table_group_members()
        self._create_table_relays()

    def execute(self, *args, **kwargs):
        return self._cursor.execute(*args, **kwargs)

    def _create_table(self, table_name, spec):
        self.execute("CREATE TABLE IF NOT EXISTS %s %s" % (table_name, spec))
        self.execute("PRAGMA user_version = %s" % (DB_VERSION,))

    def _create_index(self, index_name, table, columns):
        self.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS %s ON %s(%s)"
            % (index_name, table, columns)
        )

    def _create_table_devices(self):
        self._create_table("devices", "(ieee ieee, nwk, status)")
        self._create_index("ieee_idx", "devices", "ieee")

    def _create_table_endpoints(self):
        self._create_table(
            "endpoints",
            (
                "(ieee ieee, endpoint_id, profile_id, device_type device_type, status, "
                "FOREIGN KEY(ieee) REFERENCES devices(ieee) ON DELETE CASCADE)"
            ),
        )
        self._create_index("endpoint_idx", "endpoints", "ieee, endpoint_id")

    def _create_table_clusters(self):
        self._create_table(
            "clusters",
            (
                "(ieee ieee, endpoint_id, cluster, "
                "FOREIGN KEY(ieee, endpoint_id) REFERENCES endpoints(ieee, endpoint_id)"
                " ON DELETE CASCADE)"
            ),
        )
        self._create_index("cluster_idx", "clusters", "ieee, endpoint_id, cluster")

    def _create_table_node_descriptors(self):
        self._create_table(
            "node_descriptors",
            (
                "(ieee ieee, value, "
                "FOREIGN KEY(ieee) REFERENCES devices(ieee) ON DELETE CASCADE)"
            ),
        )
        self._create_index("node_descriptors_idx", "node_descriptors", "ieee")

    def _create_table_output_clusters(self):
        self._create_table(
            "output_clusters",
            (
                "(ieee ieee, endpoint_id, cluster, "
                "FOREIGN KEY(ieee, endpoint_id) REFERENCES endpoints(ieee, endpoint_id)"
                " ON DELETE CASCADE)"
            ),
        )
        self._create_index(
            "output_cluster_idx", "output_clusters", "ieee, endpoint_id, cluster"
        )

    def _create_table_attributes(self):
        self._create_table(
            "attributes",
            (
                "(ieee ieee, endpoint_id, cluster, attrid, value, "
                "FOREIGN KEY(ieee) "
                "REFERENCES devices(ieee) "
                "ON DELETE CASCADE)"
            ),
        )
        self._create_index(
            "attribute_idx", "attributes", "ieee, endpoint_id, cluster, attrid"
        )

    def _create_table_groups(self):
        self._create_table("groups", "(group_id, name)")
        self._create_index("group_idx", "groups", "group_id")

    def _create_table_group_members(self):
        self._create_table(
            "group_members",
            """(group_id, ieee ieee, endpoint_id,
                FOREIGN KEY(group_id) REFERENCES groups(group_id) ON DELETE CASCADE,
                FOREIGN KEY(ieee, endpoint_id)
                REFERENCES endpoints(ieee, endpoint_id) ON DELETE CASCADE)""",
        )
        self._create_index(
            "group_members_idx", "group_members", "group_id, ieee, endpoint_id"
        )

    def _create_table_relays(self):
        self._create_table(
            "relays",
            """(ieee ieee, relays,
                FOREIGN KEY(ieee) REFERENCES devices(ieee) ON DELETE CASCADE)""",
        )
        self._create_index("relays_idx", "relays", "ieee")

    def _enable_foreign_keys(self):
        self.execute("PRAGMA foreign_keys = ON")

    def _scan(self, table, filter=None):
        if filter is None:
            return self.execute("SELECT * FROM %s" % (table,))
        return self.execute("SELECT * FROM %s WHERE %s" % (table, filter))


class BasePlugin:

    def __init__(self):
        pass 

    def onStart(self):

        Domoticz.Log("onStart called")
        db = PersistingListener( "/tmp/zigpy.db" )
        Domoticz.Log("Persistent DB created")
        Domoticz.Log("%s" %db._scan('devices'))
        #time.sleep(240.0)
        
        
    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

