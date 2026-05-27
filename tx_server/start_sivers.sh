#!/bin/bash
#
# Launcher for the Sivers EVK06002 vendor shell (Eder), run on the host attached
# to the Sivers front-end. The TX servers in this folder (tx_server_zmq.py /
# tx_server_raw_tcp.py) spawn this script via `sudo ./start_sivers.sh <serial>`
# and then drive the resulting interactive `eder.py` shell.
#
# Replace <EDER_SDK_PATH> with the absolute path to your unpacked Sivers Eder
# SDK release (the directory that contains Eder_B/eder.py). The SDK is not
# redistributed with this repo — obtain it from Sivers Semiconductors.

function help {
  pushd .
  cd <EDER_SDK_PATH>/Eder_B
  python3.9 eder.py -h
  popd
}

go_rundir="cd <EDER_SDK_PATH>/Eder_B"
python_cmd="python3.9  -i eder.py"
other_opt=""
while [[ $# > 0 ]];
do
    case "$1" in
      -h|--help)        help; read -n 1 -s; exit;;
      -g|--gui)         go_rundir="cd <EDER_SDK_PATH>/Eder_B/pythonGUI"; python_cmd="python3.9 viewNotebook.py"; shift;; 
      -f=*|--fref=*)    other_opt=${other_opt}" -f ${1#*=}"; shift;;
      -f|--fref)        shift; other_opt=${other_opt}" -f ${1}"; shift;;
      -r=*|--rfm=*)     other_opt=${other_opt}" -r ${1#*=}"; shift;;
      -r|--rfm)         shift; other_opt=${other_opt}" -r ${1}"; shift;;
      -u=*|--unit=*)    other_opt=${other_opt}" -u ${1#*=}"; shift;;
      -u|--unit)        shift; other_opt=${other_opt}" -u ${1}"; shift;;
      -b=*|--board=*)   other_opt=${other_opt}" -b ${1#*=}"; shift;;
      -b|--board)       shift; other_opt=${other_opt}" -b ${1}"; shift;;
      *)                other_opt=${other_opt}" -u ${1}"; shift;;
  esac
done

{
sudo modprobe -r ftdi_sio
} &> /dev/null

export LD_LIBRARY_PATH=/usr/local/lib
$go_rundir
echo $python_cmd$other_opt
$python_cmd$other_opt