#!/usr/bin/env bash
set +e

PYTHON_BIN="python3.13"
VENV_PATH=".venv"
DATA_DIR="$(realpath ./test)"
VENV_READY=false
TLS_DIR="${DATA_DIR}/tls"

[[ ! -d "${DATA_DIR}" ]] && mkdir -p "${DATA_DIR}"

if [[ -z "${VIRTUAL_ENV}" ]]; then
  if [[ ! -d "${VENV_PATH}" ]]; then
    echo "Creating python virtual environment..."
    ${PYTHON_BIN} -m venv "${VENV_PATH}" \
    && source "${VENV_PATH}/bin/activate" \
    && pip3 install --upgrade pip \
    && pip3 install . \
    && pip3 list \
    && VENV_READY=true || VENV_READY=false
  fi
fi

[[ -x "${VENV_PATH}/bin/python3" ]] && VENV_READY=true


if ! ${VENV_READY}; then
  echo "Failed to create virtual environment."
  [[ ! -d "${VENV_PATH}" ]] && rm -rf "${VENV_PATH}"
  exit 1
else
  echo "Activating virtual environment..."
  source "${VENV_PATH}/bin/activate"
  python3 src \
  --log-level debug \
  ${@}
fi

unset TLS_CA_FILE TLS_CERT_FILE TLS_KEY_FILE
[[ -n "${VIRTUAL_ENV}" ]] && deactivate