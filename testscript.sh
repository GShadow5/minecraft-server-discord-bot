#!/bin/bash

while true; do
    read -n 1 -p "" input
    if [[ $input == "q" ]]; then
        break
    fi
    echo "hello"
    sleep 3
done
