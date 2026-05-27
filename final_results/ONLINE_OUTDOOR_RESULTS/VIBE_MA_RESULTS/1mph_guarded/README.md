# 1mph_guarded Beamforming Experiment Results

This directory contains moving average (mavg) results for the **Outdoor Adaptive Beamforming – SC** experiments conducted at **1 mph with guarded search**. The dataset corresponds to tests performed on **July 13**, with **TX gain = 9 dB**, **RX gain = 12 dB**, and a **16-meter** link distance.

---

## **Folder Structure**

Each subfolder contains results from a specific test run (`t1`–`t5`) with identical parameters but different repetitions.

```
sc_jul13_gain9db_12db_16m_t1/
sc_jul13_gain9db_12db_16m_t2/
sc_jul13_gain9db_12db_16m_t3/
sc_jul13_gain9db_12db_16m_t4/
sc_jul13_gain9db_12db_16m_t5/
```

---

## **Experiment Description**

- **Test Date:** July 13
- **TX Gain:** 9 dB
- **RX Gain:** 12 dB
- **Link Distance:** 16 meters
- **Speed:** 1 mph (simulated or controlled motion)
- **Search Method:** Guarded beam search (restricted beam index range)
- **Averaging:** Moving Average filtering applied to results


---

## **Data Contents (per test folder)**

Each test folder typically contains:
- **Raw Results** — Beam index selection logs, timestamps, and SNR measurements  

---

