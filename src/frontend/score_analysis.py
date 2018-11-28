import sys, os
import ast
import re
import numpy as np
import pickle
from subprocess import check_call
from csv import DictReader
from frontend.label_normalisation import HTSLabelNormalisation

prep_lab_scp = './scripts/prepare_labels_from_txt.sh'

glob_conf = './conf/global_settings.cfg'
ques_file = './conf/questions.hed'



IS_VOWEL = 0
NUM_SYL = 1
POS_SYL_FORWARD = 2
POS_SYL_BACKWARD = 3
NUM_PHO = 4
POS_PHO_FORWARD = 5
POS_PHO_BACKWARD = 6

n2f_csv = './note_to_lf0.csv'
FS = 16000
WS = 100
BPM = 140
BPS = BPM/60

class ScoreAnalyzer():

    def __init__(self, score_csv):
        self.score_csv = score_csv
        self.score = None
        self.note_fmap = None
        self.note_dmap = None
        self.lyric_lab_file = None
        self.words = None
        self.linguistic_feats = None
        self.init_dmap_dic()
        self.load_fmap_csv()
        self.load_score()

    def init_dmap_dic(self):
        map = {}
        map[1] = int(FS/BPS/WS*4)
        map[2] = int(FS/BPS/WS*2)
        map[4] = int(FS/BPS/WS/1)
        map[8] = int(FS/BPS/WS/2)
        map[16]= int(FS/BPS/WS/4)
        # map[1] = 100
        # map[2] = 100
        # map[4] = 100
        # map[8] = 100
        # map[16]= 100
        self.note_dmap = map

    def load_fmap_csv(self):
        with open(n2f_csv) as csvfile:
            self.note_fmap = {}
            reader = DictReader(csvfile, fieldnames=['note', 'lf0'])
            for row in reader:
                self.note_fmap[row['note']] = float(row['lf0'])

    def load_score(self):

        with open(self.score_csv) as csvfile:
            score = []
            reader = DictReader(csvfile, delimiter='|', fieldnames=['word'], restkey='syllables', skipinitialspace=True)
            for row in reader:
                # print(row)
                syls_i = row['syllables']
                # striped_notes = []
                # [striped_notes.append(ast.literal_eval(s)) for s in syllables]
                # print('*' * 20)
                # print(striped_notes)
                # print('*' * 20)
                syls_o = []
                for s in syls_i:
                    # print(s)
                    syl = []
                    for n in ast.literal_eval(s):
                        # print(n[0])
                        lf0 = self.note_fmap[n[0]]
                        syl.append([lf0, self.note_dmap[n[1]]])
                        print('notes: ')
                        print(syl)
                    syls_o.append(syl)
                row['syllables'] = syls_o
                score.append(row)
            self.score = score


    def create_lyric_lab(self, out_dir=None):
        out_lyric_path = os.path.join(out_dir, 'lyric')
        words = [i['word'].strip() for i in self.score]
        lyric = ' '.join(w for w in words)
        pid = open(out_lyric_path, 'w')
        pid.write('( lyric "{0}" )'.format(lyric))
        pid.close()
        check_call([prep_lab_scp, glob_conf, out_dir])
        self.words = words
        self.lyric_lab_file = os.path.join(out_dir, 'prompt-lab', 'lyric.lab')

    def extract_ling_feats(self):
        label_normaliser = HTSLabelNormalisation(question_file_name=ques_file,
                                                 add_frame_features=False,
                                                 subphone_feats='none')
        fid = open(self.lyric_lab_file)
        labels = fid.readlines()
        fid.close()
        # remove sil
        labels = labels[1:-1]
        feats = []
        for line in labels:
            line = line.strip()
            phone = re.split('\+', re.split('-', line)[1])[0]
            binary = label_normaliser.pattern_matching_binary(line)
            numerical = label_normaliser.pattern_matching_continous_position(line)
            feat = np.concatenate([binary, numerical], axis = 1)[0]
            assert feat[NUM_SYL] == feat[POS_SYL_FORWARD] + feat[POS_SYL_BACKWARD] - 1
            assert feat[NUM_PHO] == feat[POS_PHO_FORWARD] + feat[POS_PHO_BACKWARD] - 1
            feats.append(feat)
        self.linguistic_feats = feats

    def create_metadata(self, out_meta_file=None):
        cur_word_ind = 0
        syl_start_ind = 0
        vowel_ind = []
        syllabels_meta = []
        for i in range(len(self.linguistic_feats)):
            if self.linguistic_feats[i][IS_VOWEL]:
                vowel_ind.append(i)
            if self.linguistic_feats[i][POS_PHO_FORWARD] == 1:
                syl_start_ind = i
            if self.linguistic_feats[i][POS_PHO_FORWARD] == self.linguistic_feats[i][NUM_PHO]:
                if len(vowel_ind) != 1:
                    raise RuntimeError('Only one vowel per syllable is expected, however {0} vowel(s) detected'.format(len(vowel_ind)))
                syl_end_ind = i
                syllabels_meta.append({'start_ind': syl_start_ind, 'end_ind': syl_end_ind, 'vowel_ind': vowel_ind[0],
                                       'notes': self.score[cur_word_ind]['syllables'][int(self.linguistic_feats[i][POS_SYL_FORWARD]) - 1]})
                vowel_ind.clear()
            if (self.linguistic_feats[i][NUM_SYL] == self.linguistic_feats[i][POS_SYL_FORWARD] and
                    self.linguistic_feats[i][NUM_PHO] == self.linguistic_feats[i][POS_PHO_FORWARD]):
                if self.linguistic_feats[i][NUM_SYL] != len(self.score[cur_word_ind]['syllables']):
                    raise RuntimeError('Please specify pitch and duration for every syllable of word "{0}", '
                                       'which has {1:d} syllable(s), but you specify {2} in the score'
                                       .format(self.score[cur_word_ind]['word'], int(self.linguistic_feats[i][NUM_SYL]),
                                               len(self.score[cur_word_ind]['syllables'])))
                cur_word_ind += 1

        print('*' * 200)
        print(syllabels_meta)
        if out_meta_file:
            with open(out_meta_file, 'wb') as f:
                print(out_meta_file)
                print('INININININININININ')
                pickle.dump(syllabels_meta, f)
        else:
            return syllabels_meta


if __name__ == "__main__":



    pass
    # score = [{'word': 'you', 'syllables': [[[261, 10]]]},
             # {'word': 'are', 'syllables': [[[262, 10]]]},
             # {'word': 'beautiful', 'syllables': [  [[392, 10]], [[329, 10]], [[329, 10], [261, 30]]  ]}]


    # analyzer = ScoreAnalyzer(score)
    # analyzer.create_lyric_lab('./synth_test') # may specify in conf
    # analyzer.extract_ling_feats()
    # analyzer.create_metadata()



