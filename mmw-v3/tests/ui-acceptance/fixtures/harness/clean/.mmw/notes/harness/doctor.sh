#!/bin/sh
printf '{"pid":%s}\n' "$(cat "$MMW_DATA_DIR/pid")"
