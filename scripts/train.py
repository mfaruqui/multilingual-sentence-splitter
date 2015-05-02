import cPickle
import gzip
import os
import sys

from split_point import SplitPoint
from utils import *

if __name__=='__main__':
  gold_stats_dir = sys.argv[1]
  output_model_dir = sys.argv[2]

  os.system('mkdir -p '+output_model_dir)
  for filename in os.listdir(gold_stats_dir):
    f = gzip.open(os.path.join(gold_stats_dir, filename), 'r')
    marker = f.readline().strip()
    f.close()
    if marker in MARKERS:
      split_point = SplitPoint(marker)
      split_point.train(os.path.join(gold_stats_dir, filename))
      outfilename = filename.replace('.txt.gz', '.pkl')
      outfile = open(os.path.join(output_model_dir, outfilename), 'wb')
      cPickle.dump(split_point, outfile)
      outfile.close()
