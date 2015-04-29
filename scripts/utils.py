import re
import sys
import string

MARKERS = ['."', ".", '?','!']

LOW_LOG_PROB = -20.
LOW_VAL = 1e-5

def find_marker_occurrences(s, marker):
  index = 0
  occurrences = []
  marker_len = len(marker)
  while index < len(s):
    index = s.find(marker, index)
    if index == -1: break
    occurrences.append((marker, index, index + marker_len))
    index += marker_len
  return occurrences

def find_all_marker_occurrences(s):
  occurrences = []
  for marker in MARKERS:
    occurrences += find_marker_occurrences(s, marker)
    if marker == '."': s = s.replace('."', '')
  return occurrences

def digits_norm(text):
  return re.sub("\d", "0", text)

def get_context_of_markers_in_word(word, word_index, sent_words):
  all_marker_occ = find_all_marker_occurrences(word)
  if not all_marker_occ: return []
  all_ends = {e:0 for (m, b, e) in all_marker_occ}
  all_begs = {b:0 for (m, b, e) in all_marker_occ}

  # Split around markers first
  new_word = ''
  for index, char in enumerate(word):
    if index in all_ends or index in all_begs:
      new_word += ' '
    new_word += char

  # Split around punctuation but not markers
  word_seg = []
  for seg in new_word.split(' '):
    if re.search('\W', seg) and seg not in MARKERS:
      for c in string.punctuation:
        seg = seg.replace(c, ' '+c+' ')
      word_seg += seg.split(' ')
    else:
      word_seg.append(seg)

  while '' in word_seg:
    word_seg.remove('')

  contexts = []
  for seg_ix, segment in enumerate(word_seg):
    if segment in MARKERS:
      if seg_ix == 0:
        if word_index == 0:
          left = '<s>'
        else:
          left = sent_words[word_index - 1]
        right = word_seg[seg_ix + 1]
      elif seg_ix == len(word_seg) - 1:
        left = word_seg[seg_ix - 1]
        if word_index == len(sent_words) - 1:
          right = '</s>'
        else:
          right = sent_words[word_index + 1]
      else:
        left = word_seg[seg_ix - 1]
        right = word_seg[seg_ix + 1]
      contexts.append((segment, left, right))
    else:
      contexts.append(segment)
  return contexts
