#!/usr/bin/env bash

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 version"
  exit 1
fi

cd -- "$(dirname $0)/.."
twine upload dist/magicblue-$1.tar.gz
