import gzip
import math
import os
import re
import sys
import time

from collections import Counter
from operator import itemgetter

from utils import MARKERS, LOW_LOG_PROB, LOW_VAL
from utils import digits_norm, get_context_of_markers_in_word

class SplitPoint:
  """ Info about a possible sentence split marker """

  def __init__(self, s):
    self.marker = s  # what is the substring for split
    self.lp_yes = 0.  # Prior prob of split given marker
    self.lp_no = 0.  # Prior prob of no-split given marker
    self.lp_left_yes = Counter()  # Posterior of split of the string to left
    self.lp_right_yes = Counter()  # Post. of split of the string to right
    self.lp_left_no = Counter()  # Post. of not-split of the string to left
    self.lp_right_no = Counter()  # Post. of not-split of the string to right

  def decide_to_split(self, left, right):
    """ Model for decision making about the sentence split """

    lp_yes_split, lp_no_split = (0., 0.)

    if left in self.lp_left_yes: lp_yes_split += self.lp_left_yes[left]
    else: lp_yes_split += LOW_LOG_PROB
    if left in self.lp_left_no: lp_no_split += self.lp_left_no[left]
    else: lp_no_split += LOW_LOG_PROB

    if right in self.lp_right_yes: lp_yes_split += self.lp_right_yes[right]
    else: lp_yes_split += LOW_LOG_PROB
    if right in self.lp_right_no: lp_no_split += self.lp_right_no[right]
    else: lp_no_split += LOW_LOG_PROB

    return lp_yes_split >= lp_no_split

  def read_and_normalize(self, gold_stats_file, unsup_stats_file = None):
    """ Read the statistics computed over gold data """

    yes_split, no_split = (LOW_VAL, LOW_VAL)
    for line in gzip.open(gold_stats_file, 'r'):
      try: pattern, count, ans, position  = line.strip().split("|||")
      except: continue
      pattern, count, ans, position = (digits_norm(pattern.strip()),
      float(count.strip()), ans.strip(), position.strip())
      if position == 'left':
        if ans == 'yes':
          self.lp_left_yes[pattern] += count
          yes_split += count
        else:
          self.lp_left_no[pattern] += count
          no_split += count
      else:
        if ans == 'yes':
          self.lp_right_yes[pattern] += count
          yes_split += count
        else:
          self.lp_right_no[pattern] += count
          no_split += count

    # Normalize counts to get probabilities
    # We want this to only have gold probabilities
    self.lp_yes = math.log(yes_split / (yes_split + no_split))
    self.lp_no = math.log(no_split / (yes_split + no_split))


    sum_no = sum([val for val in self.lp_left_no.itervalues()])
    sum_no += sum([val for val in self.lp_right_no.itervalues()])

    for pattern, count in self.lp_left_no.iteritems():
      self.lp_left_no[pattern] = math.log(count / sum_no)
    for pattern, count in self.lp_right_no.iteritems():
      self.lp_right_no[pattern] = math.log(count / sum_no)

    ''' If the unsupervised wiki data is present, read it
    if unsup_stats_file:
      for line in open(unsup_stats_file, 'r'):
        try: pattern, count, position = line.strip().split("|||")
        except: continue
        pattern, count, position = (digits_norm(pattern.strip()), float(count),
                                    position.strip())
        if position == 'left':
          self.lp_left_yes[pattern] += count
        else:
          self.lp_right_yes[pattern] += count
          yes_split += count'''

    sum_yes = sum([val for val in self.lp_left_yes.itervalues()])
    sum_yes += sum([val for val in self.lp_right_yes.itervalues()])

    for pattern, count in self.lp_left_yes.iteritems():
      self.lp_left_yes[pattern] = math.log(count / sum_yes)
    for pattern, count in self.lp_right_yes.iteritems():
      self.lp_right_yes[pattern] = math.log(count / sum_yes)

    print >> sys.stderr, "Statistics read & processed for marker:", self.marker

def split_text(test_file):
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
  gold_stats_dir = 'gold-stats'
  test_file = sys.argv[1]

  split_points = {}
  for filename in os.listdir(gold_stats_dir):
    input_file = os.path.join(gold_stats_dir, filename)
    f = gzip.open(input_file, 'r')
    marker = f.readline().strip()
    if marker in MARKERS:
      split_points[marker] = SplitPoint(marker)
      split_points[marker].read_and_normalize(input_file)
  split_text(test_file)
