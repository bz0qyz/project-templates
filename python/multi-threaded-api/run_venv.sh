#!/usr/bin/env bash

PYTHON_BIN="python3.13"
VENV_PATH=".venv"
DATA_DIR="./test"

if [[ -z "${VIRTUAL_ENV}" ]]; then
  if [[ ! -d "${VENV_PATH}" ]]; then
    echo "Creating python virtual environment..."
    ${PYTHON_BIN} -m venv "${VENV_PATH}" \
    && source "${VENV_PATH}/bin/activate" \
    && pip3 install --upgrade pip \
    && pip3 install --upgrade -r ./requirements.txt
    pip3 list
  fi
fi
[[ -z "${VIRTUAL_ENV}" ]] && source "${VENV_PATH}/bin/activate"
[[ ! -d "${DATA_DIR}" ]] && mkdir -p "${DATA_DIR}"
python3 src \
  --log-level "debug" \
  --data-dir "${DATA_DIR}" \
  ${@}
[[ -n "${VIRTUAL_ENV}" ]] && deactivate