# MED9 CCP

CCP client for MED9 over J2534. Connection settings live in `.env` (see `.env.example`).

`J2534_DLL` is the full path to the PassThru DLL. `CAN_SPEED` is the bitrate in kbit/s.

## Known CCP CAN IDs

Taken from the `main.py` comments added in commit `cb51977` (`MED91` / `MED92`):

| ECU | TX (tester -> ECU) | RX (ECU -> tester) | Notes |
| --- | --- | --- | --- |
| MED9.1 | `0x7C3` | `0x7C4` | Station address used with this pair: `0x12ED` |
| MED9.2 | `0x7BC` | `0x7BD` | Commented example used a 2.0 s response timeout |
