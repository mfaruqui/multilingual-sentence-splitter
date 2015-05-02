import cPickle
import gzip
import os
import re
import sys
import time
import numpy

from collections import Counter
from operator import itemgetter

from utils import *

from split_point import SplitPoint

def split_text(split_points, test_file):
  num_sent = 0.
  start_time = time.time()

  for line in open(test_file, 'r'):
    line = line.strip().replace("''", '"')
    if not line: continue
    words = line.split()
    sent_len = len(words)

    for word_index, word in enumerate(words):
      if word in MARKERS:
        marker_obj = split_points[marker]
        if word_index > 0:
          left_word = digits_norm(words[word_index - 1])
        else:
          left_word = '<s>'
        if word_index < sent_len - 1:
          right_word = digits_norm(words[word_index + 1])
        else:
          right_word = '</s>'
        if marker_obj.decide_to_split(left_word, right_word):
          print marker
          num_sent += 1.
        else:
          print marker,
        continue

      contexts = get_context_of_markers_in_word(word, word_index, words)
      if contexts:
        new_word = ''
        for context_ix, context in enumerate(contexts):
          if not isinstance(context, str):
            marker, left, right = context
            left, right = (digits_norm(left), digits_norm(right))
            marker_obj = split_points[marker]
            if marker_obj.decide_to_split(left, right):
              new_word += marker + '\n'
              num_sent += 1.
            else:
              new_word += marker
          else:
            new_word += context
        print new_word,
        continue
      print word,

    num_sent += 1.

  end_time = time.time()
  time_taken = end_time - start_time
  print >> sys.stderr, "Processed", num_sent, "sentences in", time_taken,
  print >> sys.stderr, "seconds @", num_sent/time_taken, "sent/sec"

if __name__ == '__main__':
  models_dir = sys.argv[1]
  test_file = sys.argv[2]

  split_points = {}
  for filename in os.listdir(models_dir):
    input_file = os.path.join(models_dir, filename)
    point = cPickle.load(open(input_file, 'r'))
    if point.marker in MARKERS:
      split_points[point.marker] = point
  print >> sys.stderr, "Models loaded."
  split_text(split_points, test_file)
