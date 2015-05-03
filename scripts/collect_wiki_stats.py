import gzip
import sys
import os
import re

from collections import Counter
from operator import itemgetter

from utils import *

examples = {}
for marker in MARKERS:
  examples[marker] = Counter()

# Should the first word of this sentence be considered
# context of sentence boundary
add_first_word_to_yes = False
prev_marker = ''
prev_left = ''

for root, subFolders, files in os.walk(sys.argv[1]):
  for file in files:
    if file.endswith('.gz'): fileobj = gzip.open(os.path.join(root, file), 'r')
    else: fileobj = open(os.path.join(root, file), 'r')
    try:
      lines = fileobj.readlines()
      print >> sys.stderr, "Reading:", os.path.join(root, file)
    except:
      print >> sys.stderr, "Cant read:", os.path.join(root, file)
      continue
    for line in lines:
      line = line.strip().replace("''", '"')
      if not line or line.startswith("<"):
        continue
      words = line.split()
      num_words = len(words)
      if not num_words:
        continue

      if add_first_word_to_yes and prev_marker and prev_left:
        examples[prev_marker][(prev_left, digits_norm(words[0]), "yes")] += 1
        prev_left, prev_marker = ('', '')
        add_first_word_to_yes_right = False

      last_word = words[num_words - 1]
      if last_word in MARKERS:
        if num_words > 1:
          left = words[-2]
        else:
          continue
        add_first_word_to_yes = True
        prev_left = left
        prev_marker = last_word

      for marker in MARKERS:
        if last_word.endswith(marker):
          left = last_word.split(marker)[-2]
          add_first_word_to_yes = True
          prev_left = left
          prev_marker = marker
          break

os.system('mkdir -p wiki-stats/')
for index, marker in enumerate(MARKERS):
  outfile = open('wiki-stats/'+str(index+1)+'.txt', 'w')
  print >> outfile, marker
  for example, count in sorted(examples[marker].items(),
                               key = itemgetter(1), reverse=True):
    left, right, ans = example
    print >> outfile, left, "|||", right, "|||", ans, "|||", count

os.system('rm -f wiki-stats/*.gz')
os.system('gzip wiki-stats/*')
