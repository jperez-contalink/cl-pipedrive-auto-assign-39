#!/bin/bash

set -e

FUNCTION_NAME="cl-pipedrive-auto-assign-39"

echo "Empaquetando Lambda..."

rm -f cl-pipedrive-auto-assign-39.zip

zip -r cl-pipedrive-auto-assign-39.zip . \
  -x ".git/*" \
  -x ".gitignore" \
  -x "__pycache__/*" \
  -x "*.pyc" \
  -x "deploy.sh" \
  -x ".DS_Store" \
  -x "cl-pipedrive-auto-assign-39.zip"

echo "Subiendo a AWS..."

aws lambda update-function-code \
  --function-name "$FUNCTION_NAME" \
  --zip-file fileb://cl-pipedrive-auto-assign-39.zip

echo "Esperando actualización..."

aws lambda wait function-updated \
  --function-name "$FUNCTION_NAME"

echo "Lambda actualizado correctamente."
