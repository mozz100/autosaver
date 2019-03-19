Given the expected balance at the start of each month and the "buffer" you'd like at the end of a month, this python script
will interrogate the Starling or Monzo bank API, then calculate how much (if any) of your current balance is "spare".  If there
is spare, it will offer to save it into a savings goal (a "space", in the Starling app, or a "pot" in Monzo's terminology).

Use python 3.  Install requirements (`pip install -r requirements.txt`)

Copy settings.sample.py and fill in real values.

Then run `python main.py`.

Example output:

```
$ python ./main.py
2019-01-01 - 2019-01-31
Current balance: £377.84
Spend rate: £14.52/day
OK balance for today: £367.84
Looks like £10.00 could be saved  into 'Holiday fund'.
Target is £500.00 - this would get from £260.81 (52%) to £270.81 (54%).
Do this (enter y)? y
Done!
```

Happy saving.
