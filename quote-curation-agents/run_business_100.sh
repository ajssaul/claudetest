#!/bin/bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
cd /home/user/claudetest/quote-curation-agents
python main.py --topic "business" --count 100 --output output/result_business_100.tsv
