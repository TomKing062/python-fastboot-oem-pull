# Copyright 2014 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A libusb1-based fastboot implementation."""

import binascii
import collections
import io
import logging
import os
import struct

from adb import common
from adb import usb_exceptions

_LOG = logging.getLogger('fastboot')

DEFAULT_MESSAGE_CALLBACK = lambda m: print(m)
FastbootMessage = collections.namedtuple(  # pylint: disable=invalid-name
    'FastbootMessage', ['message', 'header'])

# From fastboot.c
VENDORS = {0x18D1, 0x0451, 0x0502, 0x0FCE, 0x05C6, 0x22B8, 0x0955,
           0x413C, 0x2314, 0x0BB4, 0x8087}
CLASS = 0xFF
SUBCLASS = 0x42
PROTOCOL = 0x03

outfile="data.out"
blocksize=4096 * 1024

DeviceIsAvailable = common.InterfaceMatcher(CLASS, SUBCLASS, PROTOCOL)

class FastbootRemoteFailure(usb_exceptions.FormatMessageWithArgumentsException):
    """Remote error."""


class FastbootStateMismatch(usb_exceptions.FormatMessageWithArgumentsException):
    """Fastboot and uboot's state machines are arguing. You Lose."""


class FastbootInvalidResponse(
    usb_exceptions.FormatMessageWithArgumentsException):
    """Fastboot responded with a header we didn't expect."""


class FastbootProtocol(object):
    """Encapsulates the fastboot protocol."""
    def __init__(self, usb, chunk_kb=1024):
        """Constructs a FastbootProtocol instance.

        Args:
          usb: UsbHandle instance.
          chunk_kb: Packet size. For older devices, 4 may be required.
        """
        self.usb = usb
        self.chunk_kb = chunk_kb

    @property
    def usb_handle(self):
        return self.usb

    def SendCommand(self, command):
        """Sends a command to the device."""
        self._Write(io.BytesIO(command), len(command))

    def HandleSimpleResponses(
            self, timeout_ms=None, info_cb=DEFAULT_MESSAGE_CALLBACK):
        """Accepts normal responses from the device.

        Args:
          timeout_ms: Timeout in milliseconds to wait for each response.
          info_cb: Optional callback for text sent from the bootloader.

        Returns:
          OKAY packet's message.
        """
        return self._AcceptResponses(info_cb, timeout_ms=timeout_ms)

    def _AcceptResponses(self, info_cb, timeout_ms=None):
        """Accepts responses until the expected header or a FAIL.

        Args:
          expected_header: OKAY or DATA
          info_cb: Optional callback for text sent from the bootloader.
          timeout_ms: Timeout in milliseconds to wait for each response.

        Raises:
          FastbootStateMismatch: Fastboot responded with the wrong packet type.
          FastbootRemoteFailure: Fastboot reported failure.
          FastbootInvalidResponse: Fastboot responded with an unknown packet type.

        Returns:
          OKAY packet's message.
        """
        while True:
            response = self.usb.BulkRead(64, timeout_ms=timeout_ms)
            header = bytes(response[:4])
            remaining = bytes(response[4:])

            if header == b'INFO':
                info_cb(FastbootMessage(remaining, header))
            elif header == b'FAIL':
                info_cb(FastbootMessage(remaining, header))
                raise FastbootRemoteFailure('FAIL: %s', remaining)
            if header == b'OKAY':
                info_cb(FastbootMessage(remaining, header))
            else:
                octets=int(remaining, 16)
                print(f"Data response, {octets} octets")
                with open(outfile, "wb") as fileout:
                    r=blocksize
                    while octets > 0:
                        if octets < blocksize:
                            r=octets
                        else:
                            print(f"{octets} remaining")
                        readdata=self.usb.BulkRead(r, timeout_ms=timeout_ms)
                        fileout.write(readdata)
                        octets-=r
            return header

    def _HandleProgress(self, total, progress_callback):
        """Calls the callback with the current progress and total ."""
        current = 0
        while True:
            current += yield
            try:
                progress_callback(current, total)
            except Exception:  # pylint: disable=broad-except
                _LOG.exception('Progress callback raised an exception. %s',
                               progress_callback)
                continue

    def _Write(self, data, length, progress_callback=None):
        """Sends the data to the device, tracking progress with the callback."""
        if progress_callback:
            progress = self._HandleProgress(length, progress_callback)
            next(progress)
        while length:
            tmp = data.read(self.chunk_kb * 1024)
            length -= len(tmp)
            self.usb.BulkWrite(tmp)

            if progress_callback and progress:
                progress.send(len(tmp))

