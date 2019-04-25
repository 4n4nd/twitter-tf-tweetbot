vegeta attack -targets=./targets.txt -name=10qps -rate=10/s -duration=180s > results.10qps.bin

vegeta plot results.10qps.bin > plot.html
