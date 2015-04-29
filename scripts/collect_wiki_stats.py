import sys
from collections import Counter
from operator import itemgetter

right = Counter()
left = Counter()

for line in sys.stdin:
  line = line.strip()
  if line.startswith('<') or not line:
    continue
  words = line.split()
  if len(words) < 4:
    continue

  right[words[0]] += 1
  if words[-1] == '.': left[words[-2]] += 1
  elif words[-1].endswith('.'): left[words[-1][0:-1]] += 1

for key, val in sorted(right.items(), key = itemgetter(1), reverse=True):
  print key, "|||", val, "|||", "right"

for key, val in sorted(left.items(), key = itemgetter(1), reverse=True):
  print key, "|||", val, "|||", "left"
