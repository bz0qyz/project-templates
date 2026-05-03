#!/usr/bin/env bash
NAME=""
DESCRIPTION=""
VERSION="1.0.0"
ENABLED=True
DFAULT_DISABLED=False
DIR_PREFIX=""

MODULES_DIR="$(dirname "$(realpath "$0")")/src/runtime/modules"
[[ ! -d "${MODULES_DIR}" ]] && { echo "Error: Modules directory not found at ${MODULES_DIR}"; exit 1; }
TEMPLATE_DIR="${MODULES_DIR}/_template"
[[ ! -d "${TEMPLATE_DIR}" ]] && { echo "Error: Template directory not found at ${TEMPLATE_DIR}"; exit 1; }

while [[ $# -gt 0 ]]; do
    key="${1}"
    case $key in
    -n|--name)
      NAME="${2}"
      shift
      shift
    ;;
    -d|--description)
      DESCRIPTION="${2}"
      shift
      shift
    ;;
    -v|--version)
      VERSION="${2}"
      shift
      shift
    ;;
    -p|--directory-prefix)
      DIR_PREFIX="${2}"
      shift
      shift
    ;;
    -MD|--disabled)
      ENABLED=True
      shift
    ;;
    -MDD|--default-disabled)
      DFAULT_DISABLED=True
      shift
    ;;
    -h|--help)
      echo "Usage: $0 -n|--name <name> -d|--description <description> [-v|--version <version>] [-e|--enabled] [-D|--default-disabled]"
      echo "Options:"
      echo "  -n, --name                Name of the module (required)"
      echo "  -d, --description         Description of the module (required)"
      echo "  -v, --version             Version of the module (default: 1.0.0)"
      echo "  -p, --directory-prefix    Directory prefix for sorting (default: none)"
      echo "  -MD, --enabled            Globally disabled (default: False)"
      echo "  -MDD, --default-disabled  Set the module as default disabled. Requires argument or ENV variable to enable (default: False)"
      exit 0
    esac
done

if [[ -z "${NAME}" || -z "${DESCRIPTION}" ]]; then
  echo "Error: Name and Description is required"
  exit 1
fi
if [[ -n ${DIR_PREFIX} && ! ${DIR_PREFIX} =~ ^-?[0-9]+$ ]]; then
  echo "Error: Directory prefix must be a number"
  exit 1
fi
# Replace spaces with hyphens in the name for the module directory
SAFE_NAME=$(echo "${NAME}" | tr ' ' '-')
ENV_NAME=$(echo "${SAFE_NAME}" | tr '-' '_')
DIR_NAME="${SAFE_NAME}"
if [[ -n "${DIR_PREFIX}" ]]; then
  DIR_NAME="${DIR_PREFIX}-${SAFE_NAME}"
fi

DESTINATION_DIR="${MODULES_DIR}/${DIR_NAME}"
if [[ -d "${DESTINATION_DIR}" ]]; then
  echo "Error: Module with name ${DIR_NAME} already exists at ${DESTINATION_DIR}"
  exit 1
fi

echo "Creating module from template:"
echo "Template: ${TEMPLATE_DIR}"
echo "Destination: ${DESTINATION_DIR}"
echo "------------------------------------------------------------"
echo "Name: ${SAFE_NAME}"
echo "Description: ${DESCRIPTION}"
echo "version ${VERSION}"
echo "Enabled: ${ENABLED}"
echo "Default Disabled: ${DFAULT_DISABLED}"
echo "------------------------------------------------------------"

cp -R "${TEMPLATE_DIR}" "${DESTINATION_DIR}"
DESTINATION_INIT="${DESTINATION_DIR}/__init__.py"
sed -i .tmp \
  -e "s/template/${SAFE_NAME}/g" \
  -e "s/TEMPLATE/$(echo ${ENV_NAME}| tr '[:lower:]' '[:upper:]')/g" \
  -e "s/\(name=\"\)[^\"]*\"/\1${SAFE_NAME}\"/" \
  -e "s/\(description=\"\)[^\"]*\"/\1${DESCRIPTION}\"/" \
  -e "s/\(version=\"\)[^\"]*\"/\1${VERSION}\"/" \
  -e "s/\(enabled=\)[^,]*/\1${ENABLED}/" \
  -e "s/\(default_disabled=\)[^,]*/\1${DFAULT_DISABLED}/" \
  "${DESTINATION_INIT}"

[[ -e "${DESTINATION_INIT}" ]] && rm -f "${DESTINATION_INIT}.tmp"
echo "Module ${SAFE_NAME} created successfully at ${DESTINATION_DIR}"