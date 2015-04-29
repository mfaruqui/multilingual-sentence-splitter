import sys
import math
import time
import re

from collections import Counter

LOW_LOG_PROB = -20

def digits_norm(text):
  return re.sub("\d", "0", text)

def evaluate(pred_list, pattern, ans_file):
  total, correct = (0., 0.)
  gold_list = []
  for gold in open(ans_file, 'r'):
    gold_list.append(gold.strip())
  assert len(gold_list) == len(pred_list)
  for gold, pred, pat in zip(gold_list, pred_list, pattern):
    if gold == pred: correct += 1.
    else: print >> sys.stderr, pat, 'Gold:', gold
    total += 1.
  print >> sys.stderr, 'Total:', len(gold_list), 'Correct:', 100 * correct/total, '%'

def find_occurrences(s, ch):
  return [i for i, letter in enumerate(s) if letter == ch]

def decide(left, right, lp_left, lp_right, lp_yes, lp_no):
  lp_yes_split, lp_no_split = (lp_yes, lp_no)

  len_left = len(left)
  if left in lp_left['yes']: lp_yes_split += lp_left['yes'][left]
  else: lp_yes_split += LOW_LOG_PROB
  if left in lp_left['no']: lp_no_split += lp_left['no'][left]
  else: lp_no_split += LOW_LOG_PROB
  '''if ('Len_l', len_left) in lp_left['yes']: lp_yes_split += lp_left['yes'][('Len_l', len_left)]
  else: lp_yes_split += LOW_LOG_PROB
  if ('Len_l', len_left) in lp_left['no']: lp_no_split += lp_left['no'][('Len_l', len_left)]
  else: lp_no_split += LOW_LOG_PROB'''

  if right: is_upper_right = right[0].isupper()
  else: is_upper_right = False
  if right in lp_right['yes']: lp_yes_split += lp_right['yes'][right]
  else: lp_yes_split += LOW_LOG_PROB
  if right in lp_right['no']: lp_no_split += lp_right['no'][right]
  else: lp_no_split += LOW_LOG_PROB
  '''if ('Cap:', is_upper_right) in lp_right['yes']:
    lp_yes_split += lp_right['yes'][('Cap:', is_upper_right)]
  else:
    lp_yes_split += LOW_LOG_PROB
  if ('Cap:', is_upper_right) in lp_right['no']:
    lp_no_split += lp_right['no'][('Cap:', is_upper_right)]
  else:
    lp_no_split += LOW_LOG_PROB'''

  return lp_yes_split > lp_no_split

def insert_newlines_in_word(word, splits):
  new_word = ''
  for j, c in enumerate(word):
    if j not in splits:
      new_word += c
    else:
      if splits[j]: new_word += '.\n'
      else: new_word += '.'
  return new_word

def read_and_normalize(gold_stats_file, unsup_stats_file):
  # Read the statistics computed over gold data
  lp_left = {'yes':Counter(), 'no':Counter()}
  lp_right = {'yes':Counter(), 'no':Counter()}
  yes_split, no_split = (0., 0.)
  for line in open(stats_file, 'r'):
    try: pattern, count, ans, position  = line.strip().split("|||")
    except: continue
    pattern, count, ans, position = (digits_norm(pattern.strip()), float(count.strip()),
                                     ans.strip(), position.strip())
    if position == 'left':
      if ans == 'yes':
        lp_left['yes'][pattern] += count
        #lp_left['yes'][('Len_l', len(pattern))] = count
        yes_split += count
      else:
        lp_left['no'][pattern] += count
        #lp_left['no'][('Len_l', len(pattern))] = count
        no_split += count
    else:
      if ans == 'yes':
        lp_right['yes'][pattern] += count
        #lp_right['yes'][('Cap:', pattern[0].isupper())] = count
        yes_split += count
      else:
        lp_right['no'][pattern] += count
        #lp_right['no'][('Cap:', pattern[0].isupper())] = count
        no_split += count

  # Normalize counts to get probabilities
  # We want this to only have gold probabilities
  lp_yes = math.log(yes_split / (yes_split + no_split))
  lp_no = math.log(no_split / (yes_split + no_split))

  sum_no = sum([val for val in lp_left['no'].itervalues()])
  sum_no += sum([val for val in lp_right['no'].itervalues()])

  for pattern, count in lp_left['no'].iteritems():
    lp_left['no'][pattern] = math.log(count / sum_no)
  for pattern, count in lp_right['no'].iteritems():
    lp_right['no'][pattern] = math.log(count / sum_no)

  # Read unsupervised sentence begining and end stats
  if unsup_stats_file:
    for line in open(unsup_stats_file, 'r'):
      try: pattern, count, position = line.strip().split("|||")
      except: continue
      pattern, count, position = (digits_norm(pattern.strip()), float(count),
                                  position.strip())
      if position == 'left':
        lp_left['yes'][pattern] += count
        #lp_left['yes'][('Len_l', len(pattern))] += count
      else:
        lp_right['yes'][pattern] += count
        #lp_right['yes'][('Cap:', pattern[0].isupper())] += count
      yes_split += count

  sum_yes = sum([val for val in lp_left['yes'].itervalues()])
  sum_yes += sum([val for val in lp_right['yes'].itervalues()])

  for pattern, count in lp_left['yes'].iteritems():
    lp_left['yes'][pattern] = math.log(count / sum_yes)
  for pattern, count in lp_right['yes'].iteritems():
    lp_right['yes'][pattern] = math.log(count / sum_yes)

  print >> sys.stderr, "Statistics read & processed."
  return lp_left, lp_right, lp_yes, lp_no

def split_text(test_file, lp_left, lp_right, lp_yes, lp_no):
  num_sent = 0.
  start_time = time.time()
  ans_list, contexts = ([], [])
  for line in open(test_file, 'r'):
    line = line.strip()
    if line.startswith('<') or not line: continue
    words = line.split()
    sent_len = len(words)

    for i, word in enumerate(words):
      if word == '.':
        if i > 0: left_word = words[i - 1]
        else: left_word = '<s>'
        if i < sent_len - 1: right_word = words[i + 1] 
        else: right_word = '</s>'
        left_word, right_word = (digits_norm(left_word), digits_norm(right_word))
        if decide(left_word, right_word, lp_left, lp_right, lp_yes, lp_no):
          print '.'
          ans_list.append("Yes")
        else:
          print '.',
          ans_list.append("No")
        contexts.append((left_word, right_word))
      elif word.find('.') != -1:
        periods_ix = find_occurrences(word, '.')
        word_len = len(word)
        splits = {}
        for ix in periods_ix:
          if ix == 0:
            if i == 0: left_word = '<s>'
            else: left_word = words[i - 1]
            right_word = word[1:]
          elif ix == word_len - 1:
            left_word = word[0:ix]
            if i < sent_len - 1: right_word = words[i+1]
            else: right_word = '</s>'
          else:
            left_word = word[0:ix]
            right_word = word[ix + 1:]
          left_word, right_word = (digits_norm(left_word), digits_norm(right_word))
          splits[ix] = decide(left_word, right_word, lp_left, lp_right, lp_yes, lp_no)
          contexts.append((left_word, right_word))
        for split_ix in splits:
          if splits[split_ix]: ans_list.append("Yes")
          else: ans_list.append("No")
        print insert_newlines_in_word(word, splits),
      else:
        print word,
    num_sent += 1.
  end_time = time.time()
  time_taken = end_time - start_time
  print >> sys.stderr, "Processed", num_sent, "sentences in", time_taken,
  print >> sys.stderr, "seconds @", num_sent/time_taken, "sent/sec"
  return ans_list, contexts
  
if __name__ == '__main__':
  if len(sys.argv) == 5:
    stats_file = sys.argv[1]
    unsup_stats_file = sys.argv[2]
    test_file = sys.argv[3]
    ans_file = sys.argv[4]
    lp_left, lp_right, lp_yes, lp_no = read_and_normalize(stats_file, unsup_stats_file)
  else:
    stats_file = sys.argv[1]
    test_file = sys.argv[2]
    ans_file = sys.argv[3]
    lp_left, lp_right, lp_yes, lp_no = read_and_normalize(stats_file, '')
  ans_list, contexts = split_text(test_file, lp_left, lp_right, lp_yes, lp_no)
  evaluate(ans_list, contexts, ans_file)
