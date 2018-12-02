from binary_io import BinaryIOCollection
import os
import numpy as np


curr_start_ind = 0
curr_end_ind = 35

prev_start_ind = 36
prev_end_ind = 71

next_start_ind = 72
next_end_ind = 107


class DataAugmentation():
    def __init__(self, ups, downs):
        self.ups = ups
        self.downs = downs

    def shift_pitch_feat(self, pitch, semi):
        ind = np.where(pitch == 1)
        assert len(ind[0]) <= 1
        if len(ind[0]) == 0:
            return
        ind = ind[0][0]
        pitch[ind] = 0
        ind = ind + semi
        assert ind >= 0 and ind <= len(pitch)
        pitch[ind] = 1

    def shift_for_one_utterance(self, utt, feat_dim, semi):
        if semi == 0:
            return os.path.basename(utt)
        io_funcs = BinaryIOCollection()
        feat, num_frame = io_funcs.load_binary_file_frame(utt, feat_dim)
        for f in feat:
            self.shift_pitch_feat(f[curr_start_ind: curr_end_ind + 1], semi)
            self.shift_pitch_feat(f[prev_start_ind: prev_end_ind + 1], semi)
            self.shift_pitch_feat(f[next_start_ind: next_end_ind + 1], semi)
        if semi > 0:
            filename = utt + '_u' + str(semi)
        else:
            filename = utt + '_d' + str(-semi)
        io_funcs.array_to_binary_file(feat, filename)
        return os.path.basename(filename)

    def lab_augmentation(self, no_silence_lab_dir):
        files = [os.path.join(no_silence_lab_dir, f) for f in os.listdir(no_silence_lab_dir) if f.endswith(".lab")]
        filenames = []
        for f in files:
            for u in range(-self.downs, self.ups + 1):
                shifted_filename = self.shift_for_one_utterance(f, 368, u)
                filenames.append(shifted_filename)
        return filenames

    def generate_dur_filename_list(self, augmented_lab_filename_list):
        return [os.path.splitext(f)[0] + '.cmp' for f in augmented_lab_filename_list]