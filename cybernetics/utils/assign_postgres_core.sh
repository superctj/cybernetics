#!/bin/bash
for pid in $(pgrep -u aditk postgres); do
  sudo taskset -cp 0 $pid
done