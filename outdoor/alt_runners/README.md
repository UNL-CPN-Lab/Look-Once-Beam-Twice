# Outdoor · Alternative-transport runners

Alternative deployment topologies for the outdoor experiment. Same algorithms as the canonical `outdoor_online_main_<variant>.py` (one folder up), but with different ways to drive the **TX-side Sivers radio**.

For the canonical ZMQ-based runners — recommended for new users — see [../outdoor_online_main_{basic,mavg,mlp}.py](../).

## When to use which

| Runner | TX location | TX transport | Use when |
|---|---|---|---|
| **`outdoor_online_main_*.py`** (canonical, parent folder) | Remote host | ZMQ REQ-REP (`tcp://<NUC_IP>:5555`) | Default. TX host runs a small ZMQ server; runner gets explicit acks per beam-set. |
| `tcp_*.py` | Remote host | Raw TCP (`<TX_HOST_IP>:5002`) | Earlier transport. Same protocol (`START_TX` handshake + `SET_TX_BEAM:<idx>` per step) but fire-and-forget bytes, no per-beam ack. |
| `usb_*.py` | Same machine as RX | None (local pexpect) | Single-host setup: both Sivers radios plugged into this host. No network at all; TX driven via `eder.tx.set_beam()` over pexpect. |

The three flavors run the **same VIBE algorithm** per variant; only the TX-control transport differs.

## Files

| File | Algorithm | Transport |
|---|---|---|
| `tcp_basic.py` | VIBE-YOLOR | Raw TCP |
| `tcp_mavg.py` | VIBE-MA | Raw TCP |
| `tcp_mlp.py` | VIBE-MLP | Raw TCP |
| `usb_basic.py` | VIBE-YOLOR | Local USB |
| `usb_mavg.py` | VIBE-MA | Local USB |
| `usb_mlp.py` | VIBE-MLP | Local USB |

## Run

```bash
cd outdoor/alt_runners
python3 tcp_mavg.py            # or any other variant
```

The scripts bootstrap their own `sys.path` so they can import `outdoor/imports.py` and the top-level `configurations/` package from this one-level-deeper location. Output paths (under `Outdoor_Adaptive_Beamforming_SC/...`) are unchanged.

## Prerequisites

Same as the canonical runners (see [../README.md](../README.md)). The TCP variants additionally require the **raw-TCP TX server** running at `<TX_HOST_IP>:5002`; the USB variants require **both Sivers radios** plugged into this host (no remote server needed). The `*_mlp.py` variants also need trained weights in [../mlp_models/](../mlp_models/).

Author: Apala Pramanik
