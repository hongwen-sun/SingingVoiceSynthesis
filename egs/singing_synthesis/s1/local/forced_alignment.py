import os, sys
import time

from sys import argv, stderr
from subprocess import check_call, Popen, CalledProcessError, PIPE
# from mean_variance_norm import MeanVarianceNorm

# string constants for various shell calls
STATE_NUM=5
F = str(0.01)
SFAC = str(5.0)
PRUNING = [str(i) for i in (250., 150., 2000.)]

MACROS = 'macros'
HMMDEFS = 'hmmdefs'
VFLOORS = 'vFloors'

##
HTKDIR = "/home/yongliang/third_party/merlin/tools/bin/htk"
HCompV = os.path.join(HTKDIR, 'HCompV')
HCopy  = os.path.join(HTKDIR, 'HCopy' )
HERest = os.path.join(HTKDIR, 'HERest')
HHEd   = os.path.join(HTKDIR, 'HHEd'  )
HVite  = os.path.join(HTKDIR, 'HVite' )

class ForcedAlignment(object):

    def __init__(self, work_dir):
        self.work_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/label"



    def prepare_training(self, wav_dir):
        print('---preparing HMM training environment')
        self.wav_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/wav"
        self.cfg_dir = os.path.join(work_dir, 'config')
        self.model_dir = os.path.join(work_dir, 'model')
        self.cur_dir = os.path.join(self.model_dir, 'hmm0')
        if not os.path.exists(self.cfg_dir):
            os.makedirs(self.cfg_dir)
        if not os.path.exists(self.cur_dir):
            os.makedirs(self.cur_dir)

        self.mfc_dir = os.path.join(work_dir, 'mfc')
        if not os.path.exists(self.mfc_dir):
            os.makedirs(self.mfc_dir)



        print('---make file_id_list.scp')
        self._make_file_id_list_scp()

        print('---make copy.scp')
        self._make_copy_scp()

        print('---mfcc extraction')
        # self._mfcc_extraction()

        print('---make proto')
        self._make_proto()

    def _make_file_id_list_scp(self):
        self.file_id_list_scp = os.path.join(self.work_dir, 'file_id_list.scp')
        fid = open(self.file_id_list_scp, 'w')
        file_id_list = []

        for f in sorted(os.listdir(self.wav_dir)):
            file_id = os.path.splitext(f)[0]
            file_id_list.append(file_id)
            fid.write(file_id + '\n')

        self.file_id_list = file_id_list
        fid.close()


    def _make_copy_scp(self):
        self.copy_scp = os.path.join(self.cfg_dir, 'copy.scp')
        copy_scp = open(self.copy_scp, 'w')
        for file_id in self.file_id_list:
            wav_file = os.path.join(self.wav_dir, file_id + '.wav')
            mfc_file = os.path.join(self.mfc_dir, file_id + '.mfc')
            if os.path.exists(wav_file):
                copy_scp.write('{0} {1}\n'.format(wav_file, mfc_file))
        copy_scp.close()


    def _mfcc_extraction(self):
        """
        Compute MFCCs
        """
        # write a CFG for extracting MFCCs
        self.copy_cfg = os.path.join(self.cfg_dir, 'copy.cfg')
        print('------make copy.cfg')
        open(self.copy_cfg, 'w').write("""SOURCEKIND = WAVEFORM
SOURCEFORMAT = WAVE
TARGETRATE = 50000.0
TARGETKIND = MFCC_D_A_0
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12
""")
        print('------extracting mfcc features...')
        check_call([HCopy, '-C', self.copy_cfg, '-S', self.copy_scp])
        # write a CFG for what we just built
        open(self.copy_cfg, 'w').write("""TARGETRATE = 50000.0
TARGETKIND = USER
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12
""")

    def _make_proto(self):
        self.proto = os.path.join(self.cfg_dir, 'proto')
        fid = open(self.proto, 'w')
        means = ' '.join(['0.0' for _ in range(39)])
        var = ' '.join(['1.0' for _ in range(39)])
        fid.write("""~o <VECSIZE> 39 <USER>
~h "proto"
<BEGINHMM>
<NUMSTATES> 7
""")
        for i in range(2, STATE_NUM+2):
            fid.write('<STATE> {0}\n\t<MEAN> 39\n\t\t{1}\n'.format(i, means))
            fid.write('\t<VARIANCE> 39\n\t\t{0}\n'.format(var))
        fid.write("""<TRANSP> 7
 0.0 1.0 0.0 0.0 0.0 0.0 0.0
 0.0 0.6 0.4 0.0 0.0 0.0 0.0
 0.0 0.0 0.6 0.4 0.0 0.0 0.0
 0.0 0.0 0.0 0.6 0.4 0.0 0.0
 0.0 0.0 0.0 0.0 0.6 0.4 0.0
 0.0 0.0 0.0 0.0 0.0 0.7 0.3
 0.0 0.0 0.0 0.0 0.0 0.0 0.0
<ENDHMM>
""")
        fid.close()




if __name__ == '__main__':

    work_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/label"
    wav_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/wav"

    # work_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/label"

    # wav_dir = "/home/yongliang/third_party/merlin/egs/singing_synthesis/s1/NIT/wav"
    # lab_dir = os.path.join(work_dir, 'label_no_align')
    # lab_align_dir = os.path.join(work_dir, 'label_state_align')

    # file_id_list_name = os.path.join(work_dir, 'file_id_list.scp')

    ## if multiple_speaker is tuned on. the file_id_list.scp has to reflact this
    ## for example
    ## speaker_1/0001
    ## speaker_2/0001
    ## This is to do speaker-dependent normalisation

    aligner = ForcedAlignment(work_dir)
    aligner.prepare_training(wav_dir)

    # aligner.train_hmm(7, 32)
    # aligner.align(work_dir, lab_align_dir)
    print('---done!')
