# attack the specified target with 10 requests per second for 180 seconds
vegeta attack -targets=./targets.txt -name=10qps -rate=10/s -duration=180s > results.10qps.bin
# Plot the output from the attack in an html
vegeta plot results.10qps.bin > plot.html
