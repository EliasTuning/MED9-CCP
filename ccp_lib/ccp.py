#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CCP (CAN Calibration Protocol) Library

Usage:
    from connection import canbus
    from ccp_lib import CCP

    bus = canbus.CANBUS()
    ccp = CCP(can=bus, tx=0x7C3, rx=0x7C4)
    ccp.connect(station_address=0x12ED)
    data = ccp.read_memory(0x0, size=4)
    print(data)
"""

import struct
from typing import Optional, List

from .protocol import CommandCodes, ReturnCodes, MTA0, MTA1


class CCPError(Exception):
    """Base exception for CCP errors."""
    pass


class CCPTimeoutError(CCPError):
    """Raised when a CCP response times out."""
    pass


class CCPResponseError(CCPError):
    """Raised when a CCP response indicates an error."""
    def __init__(self, code: ReturnCodes, message: str = ""):
        self.code = code
        super().__init__(f"CCP Error 0x{code:02X}: {code.name}" + (f" - {message}" if message else ""))


class CCP:
    """
    CCP (CAN Calibration Protocol) client implementation.
    
    Provides methods to communicate with an ECU using the CCP protocol
    over a CAN bus connection.
    """

    def __init__(self, can, tx: int, rx: int, timeout: float = 1.0):
        """
        Initialize CCP client.

        Args:
            can: CAN bus instance (must have can_send and can_recv methods)
            tx: CAN ID for transmitting messages to the ECU
            rx: CAN ID for receiving messages from the ECU
            timeout: Response timeout in seconds (default: 1.0)
        """
        self.can = can
        self.tx = tx
        self.rx = rx
        self._timeout = timeout
        self.ctr = 0x00
        self._connected = False
        self._station_address = None

    @property
    def timeout(self) -> float:
        """Get/set the response timeout in seconds."""
        return self._timeout

    @timeout.setter
    def timeout(self, value: float):
        """Set the response timeout in seconds."""
        self._timeout = value

    def _increment_ctr(self):
        """Increment the command counter (wraps at 255)."""
        self.ctr = (self.ctr + 1) & 0xFF

    def _send_cro(self, cmd: int, b0=0, b1=0, b2=0, b3=0, b4=0, b5=0):
        """
        Send a Command Receive Object (CRO) to the ECU.

        Args:
            cmd: Command code
            b0-b5: Data bytes (up to 6 bytes)
        """
        from connection.canbus import CAN_MESSAGE
        msg = CAN_MESSAGE(self.tx, [cmd, self.ctr, b0, b1, b2, b3, b4, b5])
        self.can.can_send(msg)

    def _recv_dto(self) -> Optional[bytes]:
        """
        Receive a Data Transmission Object (DTO) from the ECU.

        Returns:
            Response data bytes or None if timeout
        """
        while True:
            msg = self.can.can_recv(timeout=self.timeout)
            if msg is None:
                return None
            if msg.id == self.rx:
                return bytes(msg.data)

    def _send_command(self, cmd: int, *args) -> bytes:
        """
        Send a command and wait for response.

        Args:
            cmd: Command code
            *args: Command data bytes

        Returns:
            Response data bytes

        Raises:
            CCPTimeoutError: If no response is received
            CCPResponseError: If the ECU returns an error
        """
        # Pad args to 6 bytes
        data = list(args) + [0] * (6 - len(args))
        self._send_cro(cmd, *data[:6])
        
        response = self._recv_dto()
        if response is None:
            raise CCPTimeoutError(f"No response for command 0x{cmd:02X}")

        # Check response format: [PID, ERR, CTR, DATA...]
        pid = response[0]
        err = response[1]
        ctr = response[2]

        if err != ReturnCodes.ACKNOWLEDGE:
            try:
                return_code = ReturnCodes(err)
            except ValueError:
                return_code = err
            raise CCPResponseError(return_code)

        self._increment_ctr()
        return response

    # ========== Mandatory Commands ==========

    def connect(self, station_address: int) -> bool:
        """
        Establish a connection to the ECU.

        Args:
            station_address: ECU station address (16-bit)

        Returns:
            True if connection successful
        """
        h = (station_address & 0xFF00) >> 8
        l = station_address & 0x00FF
        response = self._send_command(CommandCodes.CONNECT, l, h)
        self._connected = True
        self._station_address = station_address
        return True

    def disconnect(self, permanent: bool = False) -> bool:
        """
        Disconnect from the ECU.

        Args:
            permanent: If True, ECU will require power cycle to reconnect

        Returns:
            True if disconnection successful
        """
        if not self._connected or self._station_address is None:
            return True

        address = struct.pack("<H", self._station_address)
        self._send_command(CommandCodes.DISCONNECT, 0x01 if permanent else 0x00, 0x00, *address)
        self._connected = False
        return True

    def get_ccp_version(self, major: int = 2, minor: int = 1) -> tuple:
        """
        Get the CCP protocol version supported by the ECU.

        Args:
            major: Requested major version
            minor: Requested minor version

        Returns:
            Tuple of (major, minor) version
        """
        response = self._send_command(CommandCodes.GET_CCP_VERSION, major, minor)
        return (response[3], response[4])

    def exchange_id(self, master_id: bytes = b'\x00\x00\x00\x00\x00\x00') -> bytes:
        """
        Exchange identification with the ECU.

        Args:
            master_id: Master device ID (up to 6 bytes)

        Returns:
            ECU response data
        """
        data = list(master_id[:6]) + [0] * (6 - len(master_id))
        response = self._send_command(CommandCodes.EXCHANGE_ID, *data)
        return response[3:]

    def set_mta(self, address: int, address_extension: int = 0x00, mta: int = MTA0) -> bool:
        """
        Set Memory Transfer Address (MTA).

        Args:
            address: 32-bit memory address
            address_extension: Address extension byte
            mta: MTA number (0 or 1)

        Returns:
            True if successful
        """
        addr_bytes = struct.pack(">L", address)
        self._send_command(CommandCodes.SET_MTA, mta, address_extension, *addr_bytes)
        return True

    def upload(self, size: int) -> bytes:
        """
        Upload (read) data from the current MTA address.

        Args:
            size: Number of bytes to read (1-5)

        Returns:
            Data bytes read from ECU memory
        """
        if size > 5:
            raise ValueError("Upload size must be <= 5 bytes per request")
        response = self._send_command(CommandCodes.UPLOAD, size)
        return response[3:3 + size]

    def dnload(self, data: bytes) -> int:
        """
        Download (write) data to the current MTA address.

        Args:
            data: Data bytes to write (1-5 bytes)

        Returns:
            New MTA address extension
        """
        if len(data) > 5:
            raise ValueError("Download data must be <= 5 bytes per request")
        size = len(data)
        padded_data = list(data) + [0] * (5 - len(data))
        response = self._send_command(CommandCodes.DNLOAD, size, *padded_data)
        return response[3]

    # ========== Memory Read/Write High-Level API ==========

    def read_memory(self, address: int, size: int = 4, address_extension: int = 0x00) -> bytes:
        """
        Read memory from the ECU at the specified address.

        This is a high-level method that handles setting the MTA and
        reading data in chunks if necessary.

        Args:
            address: 32-bit memory address to read from
            size: Number of bytes to read (default: 4)
            address_extension: Address extension byte (default: 0x00)

        Returns:
            Data bytes read from ECU memory
        """
        result = bytearray()
        current_address = address
        remaining = size

        while remaining > 0:
            # Each upload can read up to 5 bytes
            chunk_size = min(remaining, 5)
            
            # Set the memory transfer address
            self.set_mta(current_address, address_extension)
            
            # Read the data
            data = self.upload(chunk_size)
            result.extend(data)
            
            current_address += chunk_size
            remaining -= chunk_size

        return bytes(result)

    def write_memory(self, address: int, data: bytes, address_extension: int = 0x00) -> bool:
        """
        Write data to ECU memory at the specified address.

        This is a high-level method that handles setting the MTA and
        writing data in chunks if necessary.

        Args:
            address: 32-bit memory address to write to
            data: Data bytes to write
            address_extension: Address extension byte (default: 0x00)

        Returns:
            True if successful
        """
        current_address = address
        offset = 0

        while offset < len(data):
            # Each download can write up to 5 bytes
            chunk = data[offset:offset + 5]
            
            # Set the memory transfer address
            self.set_mta(current_address, address_extension)
            
            # Write the data
            self.dnload(chunk)
            
            current_address += len(chunk)
            offset += len(chunk)

        return True

    # ========== Optional Commands ==========

    def short_upload(self, address: int, size: int, address_extension: int = 0x00) -> bytes:
        """
        Short upload - read data without setting MTA first.

        Args:
            address: 32-bit memory address
            size: Number of bytes to read (1-5)
            address_extension: Address extension byte

        Returns:
            Data bytes read from ECU memory
        """
        if size > 5:
            raise ValueError("Short upload size must be <= 5 bytes")
        addr_bytes = struct.pack(">L", address)
        response = self._send_command(CommandCodes.SHORT_UP, size, address_extension, *addr_bytes)
        return response[3:3 + size]

    def get_seed(self, resource: int) -> bytes:
        """
        Request seed for unlocking a protected resource.

        Args:
            resource: Resource type to unlock

        Returns:
            Seed bytes from ECU
        """
        response = self._send_command(CommandCodes.GET_SEED, resource)
        protection_status = response[3]
        seed = response[4:8]
        return seed

    def unlock(self, key: bytes) -> int:
        """
        Send key to unlock a protected resource.

        Args:
            key: Key bytes (up to 6 bytes)

        Returns:
            Privilege status
        """
        key_data = list(key[:6]) + [0] * (6 - len(key))
        response = self._send_command(CommandCodes.UNLOCK, *key_data)
        return response[3]

    def build_checksum(self, block_size: int) -> bytes:
        """
        Calculate checksum over a memory block starting at MTA0.

        Args:
            block_size: Size of memory block in bytes

        Returns:
            Checksum bytes
        """
        size_bytes = struct.pack(">L", block_size)
        response = self._send_command(CommandCodes.BUILD_CHKSUM, *size_bytes)
        return response[3:]

    def clear_memory(self, block_size: int) -> bool:
        """
        Clear/erase a memory block starting at MTA0.

        Args:
            block_size: Size of memory block to clear

        Returns:
            True if successful
        """
        size_bytes = struct.pack(">L", block_size)
        self._send_command(CommandCodes.CLEAR_MEMORY, *size_bytes)
        return True

    def program(self, data: bytes) -> int:
        """
        Program (flash) data at the current MTA0 address.

        Args:
            data: Data bytes to program (1-5 bytes)

        Returns:
            New MTA address extension
        """
        if len(data) > 5:
            raise ValueError("Program data must be <= 5 bytes per request")
        size = len(data)
        padded_data = list(data) + [0] * (5 - len(data))
        response = self._send_command(CommandCodes.PROGRAM, size, *padded_data)
        return response[3]

    def program_6(self, data: bytes) -> int:
        """
        Program 6 bytes at the current MTA0 address.

        Args:
            data: Data bytes to program (exactly 6 bytes)

        Returns:
            New MTA address extension
        """
        if len(data) != 6:
            raise ValueError("Program_6 requires exactly 6 bytes")
        response = self._send_command(CommandCodes.PROGRAM_6, *data)
        return response[3]

    def move_memory(self, block_size: int) -> bool:
        """
        Move a memory block from MTA0 to MTA1.

        Args:
            block_size: Size of memory block to move

        Returns:
            True if successful
        """
        size_bytes = struct.pack(">L", block_size)
        self._send_command(CommandCodes.MOVE, *size_bytes)
        return True

    def test(self, station_address: int) -> bool:
        """
        Test if a station is available.

        Args:
            station_address: Station address to test

        Returns:
            True if station is available
        """
        h = (station_address & 0xFF00) >> 8
        l = station_address & 0x00FF
        try:
            self._send_command(CommandCodes.TEST, l, h)
            return True
        except CCPTimeoutError:
            return False

    def get_session_status(self) -> tuple:
        """
        Get session status.

        Returns:
            Tuple of (status, additional_info)
        """
        response = self._send_command(CommandCodes.GET_S_STATUS)
        return (response[3], response[4:])

    def set_session_status(self, status: int) -> bool:
        """
        Set session status.

        Args:
            status: Status byte

        Returns:
            True if successful
        """
        self._send_command(CommandCodes.SET_S_STATUS, status)
        return True

    def get_active_cal_page(self) -> int:
        """
        Get the currently active calibration page.

        Returns:
            Active calibration page number
        """
        response = self._send_command(CommandCodes.GET_ACTIVE_CAL_PAGE)
        return response[3]

    def select_cal_page(self) -> bool:
        """
        Select calibration page (MTA0 points to the page).

        Returns:
            True if successful
        """
        self._send_command(CommandCodes.SELECT_CAL_PAGE)
        return True

    # ========== DAQ Commands ==========

    def get_daq_size(self, daq_list_number: int, can_id: int = 0) -> tuple:
        """
        Get DAQ list size.

        Args:
            daq_list_number: DAQ list number
            can_id: CAN identifier for DAQ

        Returns:
            Tuple of (list_size, first_pid)
        """
        can_id_bytes = struct.pack(">L", can_id)
        response = self._send_command(CommandCodes.GET_DAQ_SIZE, daq_list_number, 0x00, *can_id_bytes)
        return (response[3], response[4])

    def set_daq_ptr(self, daq_list_number: int, odt_number: int, element_number: int) -> bool:
        """
        Set DAQ list pointer.

        Args:
            daq_list_number: DAQ list number
            odt_number: ODT number
            element_number: Element number within ODT

        Returns:
            True if successful
        """
        self._send_command(CommandCodes.SET_DAQ_PTR, daq_list_number, odt_number, element_number)
        return True

    def write_daq(self, element_size: int, address: int, address_extension: int = 0x00) -> bool:
        """
        Write a DAQ element.

        Args:
            element_size: Size of element in bytes
            address: Address of data to acquire
            address_extension: Address extension

        Returns:
            True if successful
        """
        addr_bytes = struct.pack(">L", address)
        self._send_command(CommandCodes.WRITE_DAQ, element_size, address_extension, *addr_bytes)
        return True

    def start_stop(self, mode: int, daq_list_number: int, last_odt_number: int,
                   event_channel: int, rate_prescaler: int) -> bool:
        """
        Start or stop a DAQ list.

        Args:
            mode: 0=stop, 1=start, 2=prepare
            daq_list_number: DAQ list number
            last_odt_number: Last ODT number to transmit
            event_channel: Event channel number
            rate_prescaler: Transmission rate prescaler

        Returns:
            True if successful
        """
        rate_bytes = struct.pack(">H", rate_prescaler)
        self._send_command(CommandCodes.START_STOP, mode, daq_list_number,
                          last_odt_number, event_channel, *rate_bytes)
        return True

    def start_stop_all(self, mode: int) -> int:
        """
        Start or stop all DAQ lists.

        Args:
            mode: 0=stop, 1=start

        Returns:
            Number of synchronized DAQ lists
        """
        response = self._send_command(CommandCodes.START_STOP_ALL, mode)
        return response[3]

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to an ECU."""
        return self._connected
