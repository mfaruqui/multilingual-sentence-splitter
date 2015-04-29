import sys
import string
from collections import Counter
from operator import itemgetter

end = Counter()
for line in sys.stdin:
  words = line.strip().split()
  if not words: continue
  #begin[words[0]] += 1
  word = words[-1]
  is_marker = True
  for c in word:
    if c not in string.punctuation:
      is_marker = False
  if is_marker: end[words[-1]] += 1

for word, count in sorted(end.items(), key=itemgetter(1), reverse=True):
  print word, "|||", count
