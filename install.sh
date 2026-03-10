#!/usr/bin/env sh
set -e

ROOT_DIR=$(cd "$(dirname "$0")" && pwd)
MODE="full"
TARGET_PATH=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --mode)
      MODE="$2"
      shift 2
      ;;
    lite|full)
      MODE="$1"
      shift
      ;;
    *)
      TARGET_PATH="$1"
      shift
      ;;
  esac
done

case "$MODE" in
  lite)
    SETTINGS_FILE="$ROOT_DIR/exmachina/openclaw.settings.lite.json"
    ;;
  full)
    SETTINGS_FILE="$ROOT_DIR/exmachina/openclaw.settings.json"
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Usage: ./install.sh [--mode lite|full] <target-config-path>"
    exit 1
    ;;
esac

if [ ! -f "$SETTINGS_FILE" ]; then
  echo "Missing: $SETTINGS_FILE"
  exit 1
fi

echo "ExMachina Prompt-First Install"
echo "1) Read: $ROOT_DIR/install/INTAKE.md"
echo "2) Select mode: $MODE"
echo "3) Import: $SETTINGS_FILE (merge only ExMachina agent entries)"
echo "4) Follow: $ROOT_DIR/exmachina/BOOTSTRAP.md"

echo ""
if [ -z "$TARGET_PATH" ]; then
  echo "Tip: You can copy the settings template into your OpenClaw config path."
  echo "Usage: ./install.sh [--mode lite|full] <target-config-path>"
  exit 0
fi

TARGET_DIR=$(dirname "$TARGET_PATH")

mkdir -p "$TARGET_DIR"
if [ -f "$TARGET_PATH" ]; then
  BACKUP_PATH="$TARGET_PATH.exmachina.bak"
  cp "$TARGET_PATH" "$BACKUP_PATH"
  echo "Backup created: $BACKUP_PATH"
fi

cp "$SETTINGS_FILE" "$TARGET_PATH"
echo "Copied settings template to: $TARGET_PATH"
echo "Note: This replaces the target file; merge manually if needed."


