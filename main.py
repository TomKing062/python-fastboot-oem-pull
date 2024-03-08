import sys
from adb import common
from adb import fastboot

DEFAULT_MESSAGE_CALLBACK = lambda m: print(m)
CLASS = 0xFF
SUBCLASS = 0x42
PROTOCOL = 0x03

DeviceIsAvailable = common.InterfaceMatcher(CLASS, SUBCLASS, PROTOCOL)
print(DeviceIsAvailable)
_handle = common.UsbHandle.FindAndOpen(DeviceIsAvailable, None, None, 1000)
_protocol = fastboot.FastbootProtocol(_handle, 1024)

_protocol.SendCommand((" ".join(sys.argv[1:])).encode('utf-8'))
print(_protocol.HandleSimpleResponses(5000, DEFAULT_MESSAGE_CALLBACK))