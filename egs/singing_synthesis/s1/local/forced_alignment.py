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
HInit = os.path.join(HTKDIR, 'HInit')
HRest = os.path.join(HTKDIR, 'HRest')
HCompV = os.path.join(HTKDIR, 'HCompV')
HCopy  = os.path.join(HTKDIR, 'HCopy' )
HERest = os.path.join(HTKDIR, 'HERest')
HHEd   = os.path.join(HTKDIR, 'HHEd'  )
HVite  = os.path.join(HTKDIR, 'HVite' )

class ForcedAlignment(object):

    def __init__(self, work_dir, NIT_dir):
        self.work_dir = work_dir
        self.NIT_dir = NIT_dir



    def prepare_training(self, wav_dir):
        print('+++preparing HMM training environment')
        self._set_path_and_dir()

        self._make_file_id_list_scp()

        self._make_copy_scp()

        self._mfcc_extraction()

        self._make_train_scp()

        self._make_proto()


    def train_hmm(self, niter, num_mix):
        print('+++training HMM models')
        self._HInit_and_HRest()
        self._HERest(niter, num_mix)

    def _set_path_and_dir(self):
        self.wav_dir = wav_dir
        self.cfg_dir = os.path.join(work_dir, 'config')
        self.model_dir = os.path.join(work_dir, 'model')
        self.compv_dir = os.path.join(self.model_dir, 'HCompV')
        self.init_dir = os.path.join(self.model_dir, 'HInit')
        self.rest_dir = os.path.join(self.model_dir, 'HRest')
        self.erest_dir = os.path.join(self.model_dir, 'HERest')
        self.mfc_dir = os.path.join(work_dir, 'mfc')
        if not os.path.exists(self.cfg_dir):
            os.makedirs(self.cfg_dir)
        if not os.path.exists(self.compv_dir):
            os.makedirs(self.compv_dir)
        if not os.path.exists(self.init_dir):
            os.makedirs(self.init_dir)
        if not os.path.exists(self.rest_dir):
            os.makedirs(self.rest_dir)
        if not os.path.exists(self.erest_dir):
            os.makedirs(self.erest_dir)
        if not os.path.exists(self.mfc_dir):
            os.makedirs(self.mfc_dir)

        self.file_id_list_scp = os.path.join(self.work_dir, 'file_id_list.scp')
        self.file_id_list = None
        self.copy_scp = os.path.join(self.cfg_dir, 'copy.scp')
        self.cfg = os.path.join(self.cfg_dir, 'copy.cfg')
        self.train_scp = os.path.join(self.cfg_dir, 'train.scp')
        self.proto = os.path.join(self.model_dir, 'proto')
        self.avg_mmf = os.path.join(self.compv_dir, 'average.mmf')
        self.cur_dir = None
        self.mono = os.path.join(self.NIT_dir, 'monophone')

    def _make_file_id_list_scp(self):
        print('---make file_id_list.scp: ' + self.file_id_list_scp)
        fid = open(self.file_id_list_scp, 'w')
        file_id_list = []

        for f in sorted(os.listdir(self.wav_dir)):
            file_id = os.path.splitext(f)[0]
            file_id_list.append(file_id)
            fid.write(file_id + '\n')

        self.file_id_list = file_id_list
        fid.close()



    def _make_copy_scp(self):
        print('---make copy.scp: ' + self.copy_scp)
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
        print('---mfcc extraction at: ' + self.mfc_dir)
        print('------make copy.cfg: ' + self.cfg)
        open(self.cfg, 'w').write("""SOURCEKIND = WAVEFORM
SOURCEFORMAT = WAVE
SOURCERATE = 625
TARGETRATE = 50000.0
TARGETKIND = MFCC_0
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12
""")
        print('------extracting mfcc features...')
        fid = open(self.cfg, 'r')
        check_call([HCopy, '-C', self.cfg, '-S', self.copy_scp])
        # write a CFG for what we just built
        open(self.cfg, 'w').write("""TARGETRATE = 50000.0
TARGETKIND = MFCC_0_D_A
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12
""")

    def _make_train_scp(self):
        # scp_path = os.path.join(des, scp_name)
        print('---make train.scp file: ' + self.train_scp)
        fid = open(self.train_scp, 'w')
        for f in sorted(os.listdir(self.mfc_dir)):
            fid.write(os.path.join(self.mfc_dir, f))
            fid.write('\n')

        fid.close()

    def _make_proto(self):
        print('---make proto: ' + self.proto)
        fid = open(self.proto, 'w')
        means = ' '.join(['0.0' for _ in range(39)])
        var = ' '.join(['1.0' for _ in range(39)])
        fid.write("""~o <VECSIZE> 39 <MFCC_0_D_A>
~h "proto"
<BEGINHMM>
<NUMSTATES> 7
""")
        for i in range(2, STATE_NUM+2):
            fid.write('<STATE> {0}\n<MEAN> 39\n {1}\n'.format(i, means))
            fid.write('<VARIANCE> 39\n {0}\n'.format(var))
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


    def _make_hmmdefs(self):
        self.hmmdefs = os.path.join(self.model_dir, 'hmmdefs')
        print('---make hmmdefs: ' + self.hmmdefs)
        hid = open(self.hmmdefs, 'w')
        pid = open(self.proto, 'r')
        mid = open(self.mono, 'r')

        hid.write(pid.readline())
        pid.readline() #remove "~h" line
        proto = pid.readlines()
        for phone in mid.readlines():
            phone = phone.strip()
            hid.write('~h "{0}"\n'.format(phone))
            hid.writelines(proto)
        hid.write('\n')

        hid.close()
        pid.close()
        mid.close()

    def _HCompV(self):
        check_call([HCompV, '-A', '-D', '-T', str(1),
                    '-S', self.train_scp,
                    '-m',
                    '-C', self.cfg,
                    '-M', self.compv_dir,
                    '-o', self.avg_mmf,
                    self.proto])

    def _HInit_and_HRest(self):
        print('-+-stage 1: HInit & HRest')
        fid = open(self.mono)
        for p in fid.readlines():
            p = p.strip()
            check_call([HInit, '-A', '-D', '-T', str(1),
                        '-S', self.train_scp,
                        '-M', self.init_dir,
                        '-m', str(1),
                        '-C', self.cfg,
                        '-L', os.path.join(self.NIT_dir, 'mono'),
                        '-l', p,
                        '-o', p,
                        self.proto])
            check_call([HRest, '-A', '-D', '-T', str(1),
                        '-S', self.train_scp,
                        '-M', self.rest_dir,
                        '-m', str(1),
                        '-C', self.cfg,
                        '-L', os.path.join(self.NIT_dir, 'mono'),
                        '-l', p,
                        os.path.join(self.init_dir, p)])
        hmmdefs = os.path.join(self.rest_dir, HMMDEFS)
        if not os.path.exists(hmmdefs):
            os.system("cd {0}; cat * > hmmdefs".format(self.rest_dir))
        self.cur_dir = self.rest_dir

    def _HERest(self, niter, num_mix):
        print('-+-stage 2: HERest')
        done = 0
        mix = 1
        while mix <= num_mix and done == 0:
            for i in range(niter):
                next_dir = os.path.join(self.erest_dir, 'hmm_mix_' + str(mix) + '_iter_' + str(i+1))
                if not os.path.exists(next_dir):
                    os.makedirs(next_dir)
                check_call([HERest, '-A', '-D', '-T', str(1),
                            '-S', self.train_scp,
                            '-C', self.cfg,
                            '-L', os.path.join(self.NIT_dir, 'mono'),
                            '-M', next_dir,
                            '-m', str(1),
                            '-H', os.path.join(self.cur_dir, HMMDEFS),
                            '-t'] + PRUNING + [self.mono],
                            stdout=PIPE)
                self.cur_dir = next_dir

                if mix * 2 <= num_mix:
                    ##increase mixture number
                    hed_file = os.path.join(self.cfg_dir, 'mix_' + str(mix * 2) + '.hed')
                    fid = open(hed_file, 'w')
                    fid.write('MU ' + str(mix * 2) + ' {*.state[2-'+str(STATE_NUM+2)+'].mix}\n')
                    fid.close()

                    next_dir = os.path.join(self.erest_dir, 'hmm_mix_' + str(mix * 2) + '_iter_0')
                    if not os.path.exists(next_dir):
                        os.makedirs(next_dir)

                    check_call( [HHEd, '-A', '-D', '-T', str(1),
                                '-H', os.path.join(self.cur_dir, HMMDEFS),
                                '-M', next_dir] + [hed_file] + [self.mono])

                    self.cur_dir = next_dir
                    mix = mix * 2
                else:
                    done = 1



if __name__ == '__main__':


    # work_dir = sys.argv[1]
    # wav_dir = sys.argv[2]
    # NIT_dir = sys.argv[3]
    NIT_dir = sys.argv[1]
    wav_dir = os.path.join(NIT_dir, 'wav')
    work_dir = os.path.join(NIT_dir, 'label')


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

    aligner = ForcedAlignment(work_dir, NIT_dir)
    aligner.prepare_training(wav_dir)

    aligner.train_hmm(7, 32)
    # aligner.align(work_dir, lab_align_dir)
    print('---done!')
