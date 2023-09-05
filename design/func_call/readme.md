# Function Calls

## Updates to wait on first output

## How to Call

### On next (generator)

1. Caller grounds wait signal
2. Stalls until ready signal is high
3. When ready is high, captures output (currently not nessessary)
4. Holds wait signal
5. Continues logic
