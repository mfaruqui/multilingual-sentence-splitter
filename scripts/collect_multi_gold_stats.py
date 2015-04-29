import sys
import os

from collections import Counter
from operator import itemgetter

from utils import MARKERS
from utils import find_marker_occurrences, find_all_marker_occurrences
from utils import get_context_of_markers_in_word, digits_norm

yes_right, yes_left, no_right, no_left = ({}, {}, {}, {})

for marker in MARKERS:
  # Words occurring around a sentence boundary period
  yes_right[marker] = Counter()
  yes_left[marker] = Counter()

  # Words occurring around a non-breaking period
  no_right[marker] = Counter()
  no_left[marker] = Counter()

# Should the first word of this sentence be considered
# right context of sentence boundary
add_first_word_to_yes_right = False
prev_marker = ''

for line in sys.stdin:
  line = line.strip().replace("''", '"')
  line = re.sub('\.\s+"', '."', line)
  words = line.split()

  try: words.remove("")
  except: pass
  if len(words) < 4: continue

  if add_first_word_to_yes_right and prev_marker:
    yes_right[prev_marker][digits_norm(words[0])] += 1.
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
        yes_left[word][left] += 1.
        add_first_word_to_yes_right = True
        prev_marker = word
      # not a sentence boundary
      else:
        if word_index > 0:
          left = digits_norm(words[word_index - 1])
          no_left[word][left] += 1.
        right = digits_norm(words[word_index + 1])
        no_right[word][right] += 1.
    else:
      contexts = get_context_of_markers_in_word(word, word_index, words)
      for context_ix, context in enumerate(contexts):
        if not isinstance(context, str):
          marker, left, right = context
          left, right = (digits_norm(left), digits_norm(right))
          # If this is a sentence end
          if context_ix == len(contexts) - 1 and sent_end:
            yes_left[marker][left] += 1.
            add_first_word_to_yes_right = True
            prev_marker = marker
          else:
            no_left[marker][left] += 1.
            no_right[marker][right] += 1.

num = 1
for marker in MARKERS:
  outfile = open('gold-stats/'+str(num)+'.txt', 'w')
  print >> outfile, marker
  for key, val in sorted(yes_right[marker].items(), key = itemgetter(1), reverse=True):
    print >> outfile, key, "|||", val, "||| yes ||| right"

  for key, val in sorted(no_right[marker].items(), key = itemgetter(1), reverse=True):
    print >> outfile, key, "|||", val, "||| no ||| right"

  for key, val in sorted(yes_left[marker].items(), key = itemgetter(1), reverse=True):
    print >> outfile, key, "|||", val, "||| yes ||| left"

  for key, val in sorted(no_left[marker].items(), key = itemgetter(1), reverse=True):
    print >> outfile, key, "|||", val, "||| no ||| left"
  num += 1

os.system('rm -f gold-stats/*.gz')
os.system('gzip gold-stats/*')
