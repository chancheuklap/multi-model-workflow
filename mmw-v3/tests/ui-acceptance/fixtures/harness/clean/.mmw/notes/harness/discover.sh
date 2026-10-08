#!/bin/sh
printf %s "{\"origin\":\"http://127.0.0.1:$MMW_PORT_BASE\",\"instance\":\"demo\",\"instance_check\":\"GET /health -> ok\"}"
