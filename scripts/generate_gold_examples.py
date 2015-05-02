import sys
import os
import re

from collections import Counter
from operator import itemgetter

from utils import MARKERS
from utils import find_marker_occurrences, find_all_marker_occurrences
from utils import get_context_of_markers_in_word, digits_norm

examples = {}
for marker in MARKERS:
  examples[marker] = Counter()

# Should the first word of this sentence be considered
# context of sentence boundary
add_first_word_to_yes = False
prev_marker = ''
prev_left = ''

for line in sys.stdin:
  line = line.strip().replace("''", '"')
  if not line: continue
  words = line.split()

  if add_first_word_to_yes and prev_marker and prev_left:
    examples[prev_marker][(prev_left, digits_norm(words[0]), "yes")] += 1
    prev_left, prev_marker = ('', '')
    add_first_word_to_yes_right = False

  num_words = len(words)
  for word_index, word in enumerate(words):
    if word_index == num_words - 1:
      sent_end = True
    else:
      sent_end = False

    # If the word is a marker
    if word in MARKERS:
      # If this is a sentence boundary
      if sent_end:
        left = digits_norm(words[word_index - 1])
        add_first_word_to_yes = True
        prev_marker = word
        prev_left = left
      # not a sentence boundary
      else:
        if word_index > 0:
          left = digits_norm(words[word_index - 1])
        else:
          left = "</s>"
        right = digits_norm(words[word_index + 1])
        examples[word][(left, right, "no")] += 1
    else:
      contexts = get_context_of_markers_in_word(word, word_index, words)
      for context_ix, context in enumerate(contexts):
        if not isinstance(context, str):
          marker, left, right = context
          left, right = (digits_norm(left), digits_norm(right))
          # If this is a sentence end
          if context_ix == len(contexts) - 1 and sent_end:
            add_first_word_to_yes = True
            prev_marker = marker
            prev_left = left
          else:
            examples[marker][(left, right, "no")] += 1

os.system('mkdir -p gold-stats/')
for index, marker in enumerate(MARKERS):
  outfile = open('gold-stats/'+str(index+1)+'.txt', 'w')
  print >> outfile, marker
  for example, count in sorted(examples[marker].items(),
                               key = itemgetter(1), reverse=True):
    left, right, ans = example
    print >> outfile, left, "|||", right, "|||", ans, "|||", count

os.system('rm -f gold-stats/*.gz')
os.system('gzip gold-stats/*')
