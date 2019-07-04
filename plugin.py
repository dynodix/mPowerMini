# Basic Python Plugin Example
#
# Author: Dynodix
#
# need curl on linux (apt-get install curl)
"""
<plugin key="mPowerMini" name="mFI mPower mini 1 socket" author="dynodix" version="1.3.0">
    <params>
            <param field="Address" label="IP Address" width="200px" required="true" default="127.0.0.1"/>
            <param field="Port" label="Port" width="30px" required="true" default="80"/>
            <param field="Mode1" label="Username" width="100px" required="true" default="Admin"/>
            <param field="Mode2" label="Password" width="100px" required="true" default=""/>
            <param field="Mode6" label="Debug" width="75px">
                <options>
                    <option label="True" value="Debug"/>
                    <option label="False" value="Normal"  default="true" />
                </options>
            </param>
    </params>
</plugin>
"""
import Domoticz
import subprocess
import json

class BasePlugin:
    enabled = False
    pluginState = "Not Ready"
    sessionCookie = ""
    privateKey = b""
    socketOn = "FALSE"


    def __init__(self):
        return

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
             Domoticz.Debugging(1)
        if (len(Devices) == 0):
             Domoticz.Device(Name="Socket ", Unit=1, TypeName="Switch", Image=1 ).Create()
             Domoticz.Log("Switch Device created.")
             Domoticz.Device(Name="Voltage", Unit=2, TypeName="Voltage").Create()
             Domoticz.Log("Voltage Device created.")
             Domoticz.Device(Name="Amperage", Unit=3, TypeName= "Current (Single)").Create()
             Domoticz.Log("Ampermeter Device created.")
        DumpConfigToLog()
#        Domoticz.Transport(Transport="TCP/IP", Address=Parameters["Address"], Port=Parameters["Port"])
#        Domoticz.Protocol("HTTP")
        # seconds for recconect and report
        Domoticz.Heartbeat(30)
#        Domoticz.Connect()
        self.sessionCookie = "01234567890123456789012345678901"
        if (1 in Devices) and (Devices[1].nValue == 1):
            self.socketOn = "TRUE"
        Domoticz.Debug("onStart called")

    def onStop(self):
        Domoticz.Debug("onStop called")


    def onConnect(self, Status, Description):
        Domoticz.Log("onConnect called")
        self.mPowerLogin()
        if (Status == 0):
            Domoticz.Log("mPower connected successfully.")
#            self.mPowerLogin()
#            self.pluginState = "GetAuth"
        else:
            self.pluginState = "Not Ready"
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"])
            Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Parameters["Address"]+":"+Parameters["Port"]+" with error: "+Description)

    def onMessage(self, Data, Status, Extra):
        Domoticz.Debug("on Message called , Session coockie is :"+self.sessionCookie)

    def onCommand(self, Unit, Command, Level, Hue):
        if Command == 'Off' :
           sendcmd = 0
           Devices[1].Update(0,'Off')
        else :
           sendcmd = 1
           Devices[1].Update(1,'On')
        self.mPowerSwitch(sendcmd)
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        # write here the switch on command

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
#        if (self.pluginState == "Not Ready"):
#            Domoticz.Log("onHeartbeat plugin not ready")
        self.mPowerGetValues()
        Domoticz.Debug("onHeartbeat called")

    def mPowerLogin(self):
        Domoticz.Debug("LOGIN curl")
        mPowercmd = 'curl --connect-timeout 19 -X POST -d "username='+Parameters["Mode1"]+'&password='+Parameters["Mode2"]+'" -b "AIROS_SESSIONID='+self.sessionCookie+'" '+Parameters["Address"]+'/login.cgi'
        mResult = subprocess.Popen(mPowercmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        Domoticz.Debug("CURL SEND "+ mPowercmd)
        Domoticz.Debug("CURL RECEIVED "+ str(mResult))
        return

    def mPowerLogout(self):
        Domoticz.Debug("LOGOUT curl")
        mPowercmd = 'curl --connect-timeout 19 -b "AIROS_SESSIONID='+self.sessionCookie+'" '+Parameters["Address"]+'/logout.cgi'
        mResult = subprocess.Popen(mPowercmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        Domoticz.Debug("LOGOUT SENT "+ str(mResult))
        return

    def mPowerSwitch(self , switching):
        Domoticz.Debug("SWITCH MODE")
#curl --silent -X PUT -d output=0 -b "AIROS_SESSIONID="$SESSIONID 192.168.4.22/sensors/1 > /dev/null
        mPowercmd = 'curl --silent -X PUT -d output='+str(switching)+' -b "AIROS_SESSIONID='+self.sessionCookie+'" '+Parameters["Address"]+'/sensors/1'
        mResult = subprocess.Popen(mPowercmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        mResult = mResult.decode("utf-8")
        Domoticz.Debug("SWITCH SWITCH "+ mPowercmd)
        return

    def mPowerGetValues(self):
        Domoticz.Debug("SENSORS Queried")
        mPowercmd = 'curl --connect-timeout 19 -b "AIROS_SESSIONID='+self.sessionCookie+'" '+Parameters["Address"]+'/sensors'
        mResult = subprocess.Popen(mPowercmd, shell=True, stdout=subprocess.PIPE).stdout.read()
        mResult = mResult.decode("utf-8")
        Domoticz.Debug("CURL SEND "+ mPowercmd)
        Domoticz.Debug("CURL RECEIVED "+ str(mResult))
        if len(str(mResult)) > 6 :
            pjs = json.loads(str(mResult))
            if pjs['status']=='success':
                pjs = pjs['sensors'][0]
                self.mPowerDevUpdate(2,0,'%.3f' % float(pjs['voltage']))
                self.mPowerDevUpdate(3,0,'%.3f' % float(pjs['current']))
                if pjs['output']==1 :
                    self.mPowerDevUpdate(1,1,'On')
                else :
                   self.mPowerDevUpdate(1,0,'Off')
        else :
            Domoticz.Log(Devices[1].Name+" SEEMS disconnected. Trying to recconect")
            self.mPowerLogout()
            self.mPowerLogin()
        return

    def mPowerDevUpdate(self , Unit , nValue, sValue):
        if (Unit in Devices):
           if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
              Devices[Unit].Update(nValue, sValue)
              Domoticz.Debug("Update "+str(nValue)+":'"+sValue+"' ("+Devices[Unit].Name+")")

        return


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Status, Description):
    global _plugin
    _plugin.onConnect(Status, Description)

def onMessage(Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect():
    global _plugin
    _plugin.onDisconnect()

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