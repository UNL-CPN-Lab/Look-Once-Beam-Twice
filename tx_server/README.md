# TX-side servers

These two scripts run on the **transmitter (TX) host** — the machine physically attached to the Sivers TX front-end. They spawn the Sivers TX shell once, then sit in a loop answering beam-control commands from the UE-side runners over the network. The UE host never touches the TX radio directly; it sends commands here.

The two files are functionally identical and differ only in transport:

| File | Transport | Port | Used by |
|---|---|---|---|
| [tx_server_zmq.py](tx_server_zmq.py) | ZMQ REP socket | 5555 | the canonical runners [outdoor/outdoor_online_main_*.py](../outdoor/) |
| [tx_server_raw_tcp.py](tx_server_raw_tcp.py) | raw TCP socket | 5002 | the alternate runners [outdoor/alt_runners/tcp_*.py](../outdoor/alt_runners/) and [outdoor/fullsweep/](../outdoor/fullsweep/) |

## Protocol

Both servers accept the same text commands and reply with a short status string:

| Command | Action | Reply |
|---|---|---|
| `START_TX` | init Sivers, set 60.48 GHz, enable TX, set baseband/RF gains | `TX_READY` |
| `SET_TX_BEAM:<idx>` | `eder.tx.set_beam(<idx>)` | `TX_BEAM_SET:<idx>` |
| `STOP_TX` | disable TX, close log | `TX_STOPPED` |

## Running

Start the matching server on the TX host **before** launching the UE-side runner:

```bash
# ZMQ (matches outdoor_online_main_*.py)
python3 tx_server/tx_server_zmq.py

# or raw TCP (matches the tcp_* / fullsweep runners)
python3 tx_server/tx_server_raw_tcp.py
```

Each server spawns `sudo ./start_sivers.sh <serial>` to bring up the Sivers Eder shell, then drives it. The server also adds the repo root to `sys.path`, so it imports `configurations.utils` regardless of the directory it is launched from.

### Before running

- Edit [start_sivers.sh](start_sivers.sh): set `<EDER_SDK_PATH>` to your unpacked Sivers Eder SDK (the folder containing `Eder_B/eder.py`).
- Provide the Sivers TX serial passed to the launcher (the placeholder `<SIVERS_TX_SERIAL_ALT>` in `start_sivers_transmitter`).
- Provide the sudo password the script sends at the `[sudo] password for ...` prompt (placeholder `<SUDO_PASSWORD>`).
- Make sure the UE-side runner points at this host's IP and the matching port (5555 for ZMQ, 5002 for raw TCP).

Author: Avhishek Biswas and Apala Pramanik
