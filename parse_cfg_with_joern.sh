#!/bin/bash

set -e

# Set these paths as needed
JOERN_PATH=/usr/local/bin
CODE_DIR=test_repo
CODE_DIR_ABS="$(cd "$(dirname "$CODE_DIR")"; pwd)/$(basename "$CODE_DIR")"
WORKSPACE=joern_workspace
OUT_DIR=out

# Check if Joern exists
if [ ! -x "$JOERN_PATH/joern" ]; then
  echo "Error: Joern not found at $JOERN_PATH/joern."
  echo "Please set JOERN_PATH in this script to the directory where Joern is installed."
  exit 1
fi

# Check if test_repo exists
if [ ! -d "$CODE_DIR_ABS" ]; then
  echo "Error: Code directory $CODE_DIR_ABS not found."
  echo "Please make sure test_repo exists in the current directory."
  exit 1
fi

# 1. Clean up previous workspace and output
echo "Cleaning up previous workspace and output..."
rm -rf $WORKSPACE $OUT_DIR
mkdir $WORKSPACE
mkdir $OUT_DIR

# 2. Run Joern to generate and export CFG using the official plugin
echo "Importing code and exporting CFG using dumpcfg plugin..."
$JOERN_PATH/joern --run dumpcfg --src $CODE_DIR --language python --store

echo "CFG export completed. Check $OUT_DIR/ for .dot files."