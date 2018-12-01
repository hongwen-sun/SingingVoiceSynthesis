import sys, os, errno
from csv import DictReader
import ast
sys.path.insert(0, '../../../src')
from frontend.score_analysis import ScoreAnalyzer

if __name__ == '__main__':

    score = 'score'

    in_score = sys.argv[1]
    out_dir = sys.argv[2]
    singing_inter_data_dir = os.path.join(out_dir, 'singing')

    try:
        os.makedirs(singing_inter_data_dir)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise

    if not os.path.exists(singing_inter_data_dir):
        os.makedirs(singing_inter_data_dir)

    analyzer = ScoreAnalyzer(score)
    analyzer.create_lyric_lab(out_dir)
    analyzer.extract_ling_feats()
    analyzer.create_metadata(os.path.join(singing_inter_data_dir, 'meta'))
