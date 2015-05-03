import gzip
import math
import os
import re
import sys
import time
import numpy

from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import BernoulliNB

from scipy.sparse import csr_matrix, dok_matrix, vstack

from collections import Counter
from operator import itemgetter

from utils import *

class SplitPoint:
  """ Info about a possible sentence split marker """

  def __init__(self, s):
    self.marker = s  # what is the substring for split
    self.features = {} # mapping features to an index integer
    self.decision_model = LogisticRegression() #BernoulliNB is very slow

  def featurize(self, features):
    """ Featurize the data point """

    feat_vec = numpy.zeros(len(self.features))
    for feat in features:
      if feat in self.features:
        feat_vec[self.features[feat]] = 1.
    return feat_vec

  def decide_to_split(self, left, right):
    """ Model for decision making about the sentence split """

    # If the model could not be trained: split
    if not self.features:
      return True

    feat_vec = self.featurize(generate_features(self.marker, left, right))
    if self.decision_model.predict(feat_vec) == 1:
      return True
    else:
      return False

  def train(self, gold_stats_file):
    """ Read the statistics computed over gold data """

    temp_data = []
    num_examples = 0.
    for line in gzip.open(gold_stats_file, 'r'):
      try: left, right, ans, count = line.strip().split("|||")
      except: continue
      left, right, ans, count = (digits_norm(left.strip()),
                                 digits_norm(right.strip()),
                                 ans.strip(), int(count))
      f = generate_features(self.marker, left, right)
      for feat in f:
        if feat not in self.features:
          self.features[feat] = len(self.features)
      temp_data.append((f, ans, count))
      num_examples += count

    X, Y = (dok_matrix((num_examples, len(self.features))), [])
    index = 0
    for f, ans, count in temp_data:
      for i in range(count):
        for feat in f:
          X[index, self.features[feat]] = 1
        index += 1
        if ans == 'yes': Y.append(1)
        else: Y.append(0)
    del temp_data

    # IF Training Data Exists
    if self.features:
      self.decision_model.fit(csr_matrix(X), Y)
