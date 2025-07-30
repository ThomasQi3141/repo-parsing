#!/bin/bash

set -e

# Set these paths as needed
JOERN_PATH=/usr/local/bin
CODE_DIR=repos/test_repo
OUT_DIR=out

# Check if Joern exists
if [ ! -x "$JOERN_PATH/joern" ]; then
  echo "Error: Joern not found at $JOERN_PATH/joern."
  echo "Please set JOERN_PATH in this script to the directory where Joern is installed."
  exit 1
fi

# Check if code directory exists
if [ ! -d "$CODE_DIR" ]; then
  echo "Error: Code directory $CODE_DIR not found."
  echo "Please make sure the code directory exists in the current directory."
  exit 1
fi

# 1. Clean up previous output
echo "Cleaning up previous output..."
rm -rf $OUT_DIR
mkdir $OUT_DIR

# 2. Run Joern to generate and export CFG and call graph using the official plugins
echo "Importing code and exporting CFG using dumpcfg plugin..."
$JOERN_PATH/joern --src $CODE_DIR --language python --overwrite --run dumpcfg

echo "Exporting call graph using callgraph plugin..."
$JOERN_PATH/joern --src $CODE_DIR --language python --overwrite --run callgraph

echo "CFG and call graph export completed. Check $OUT_DIR/ for .dot files."