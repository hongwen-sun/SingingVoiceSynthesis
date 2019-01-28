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

    def __init__(self, work_dir, wav_dir, full_dir, mono_dir, phones, lab_dir):
        self.work_dir = work_dir
        self.wav_dir = wav_dir
        self.full_dir = full_dir
        self.mono_dir = mono_dir
        self.phones = phones
        self.lab_dir = lab_dir

    def prepare_training(self):
        # print('+++preparing HMM training environment')
        self._set_path_and_dir()

        self._make_file_id_list_scp()

        self._make_copy_scp()

        self._mfcc_extraction()

        self._make_train_scp()

        self._make_proto()

        self._make_phoneme_map()

        self._make_mono_no_align()


    def train_hmm(self, niter, num_mix):
        print('+++training HMM models')
        self._HInit_and_HRest()
        self._HERest(niter, num_mix)

    # def align(self, lab_align_dir):
    def align(self):
        """
        Align using the models in self.cur_dir and MLF to path
        """
        print('---aligning data')
        print(time.strftime("%c"))

        self.cur_dir = os.path.join(self.erest_dir, 'hmm_mix_32_iter_7')

        check_call([HVite, '-A', '-D', '-T', str(1),
                    '-a', '-f', '-m', '-y', 'lab', '-o', 'SM',
                    '-i', self.align_res_mlf, '-L', self.mono_no_align_dir,
                    '-C', self.cfg, '-S', self.train_scp,
                    '-H', os.path.join(self.cur_dir, HMMDEFS),
                    '-I', self.mono_no_align_mlf, '-t'] + PRUNING +
                   ['-s', SFAC, self.phoneme_map, self.phones])

        self._postprocess()
        print('Success! Aligned labels are in: ', self.lab_dir)

    def _set_path_and_dir(self):
        self.cfg_dir = os.path.join(self.work_dir, 'config')
        self.model_dir = os.path.join(self.work_dir, 'model')
        self.compv_dir = os.path.join(self.model_dir, 'HCompV')
        self.init_dir = os.path.join(self.model_dir, 'HInit')
        self.rest_dir = os.path.join(self.model_dir, 'HRest')
        self.erest_dir = os.path.join(self.model_dir, 'HERest')
        self.mfc_dir = os.path.join(self.work_dir, 'mfc')
        self.mono_no_align_dir = os.path.join(self.work_dir, 'mono_no_align')
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
        if not os.path.exists(self.mono_no_align_dir):
            os.makedirs(self.mono_no_align_dir)
        if not os.path.exists(self.lab_dir):
            os.makedirs(self.lab_dir)

        self.file_id_list_scp = os.path.join(self.work_dir, 'file_id_list.scp')
        self.file_id_list = None
        self.copy_scp = os.path.join(self.cfg_dir, 'copy.scp')
        self.cfg = os.path.join(self.cfg_dir, 'cfg')
        self.train_scp = os.path.join(self.cfg_dir, 'train.scp')
        self.proto = os.path.join(self.model_dir, 'proto')
        self.avg_mmf = os.path.join(self.compv_dir, 'average.mmf')
        self.cur_dir = None
        self.align_res_mlf = os.path.join(self.work_dir, 'mono_align.mlf')
        self.phoneme_map = os.path.join(self.work_dir, 'phoneme_map.dict')
        self.mono_no_align_mlf = os.path.join(self.cfg_dir, 'mono_no_align.mlf')

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
        mid = open(self.phones, 'r')

        hid.write(pid.readline())
        pid.readline() #remove "~h" line
        proto = pid.readlines()
        for p in mid.readlines():
            p = p.strip()
            hid.write('~h "{0}"\n'.format(p))
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
        fid = open(self.phones)
        for p in fid.readlines():
            p = p.strip()
            check_call([HInit, '-A', '-D', '-T', str(1),
                        '-S', self.train_scp,
                        '-M', self.init_dir,
                        '-m', str(1),
                        '-C', self.cfg,
                        '-L', self.mono_dir,
                        '-l', p,
                        '-o', p,
                        self.proto])
            check_call([HRest, '-A', '-D', '-T', str(1),
                        '-S', self.train_scp,
                        '-M', self.rest_dir,
                        '-m', str(1),
                        '-C', self.cfg,
                        '-L', self.mono_dir,
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
                            '-L', self.mono_dir,
                            '-M', next_dir,
                            '-m', str(1),
                            '-H', os.path.join(self.cur_dir, HMMDEFS),
                            '-t'] + PRUNING + [self.phones],
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
                                '-M', next_dir] + [hed_file] + [self.phones])

                    self.cur_dir = next_dir
                    mix = mix * 2
                else:
                    done = 1

    def _make_phoneme_map(self):
        print('---make phoneme map: ' + self.phoneme_map)
        pid = open(self.phones, 'r')
        mid = open(self.phoneme_map, 'w')
        for p in pid.readlines():
            p = p.strip()
            mid.write('{0} {1}\n'.format(p, p))
        pid.close()
        mid.close()

    def _make_mono_no_align(self):
        print('---make mono phoneme label file (without alignment) at: ' + self.mono_no_align_dir)
        print('---make mono no align mlf file: ' + self.mono_no_align_mlf)
        for file_id in self.file_id_list:
            full_label = os.path.join(self.full_dir, file_id + '.lab')
            mono_label = os.path.join(self.mono_no_align_dir, file_id + '.lab')
            fid = open(full_label, 'r')
            mid = open(mono_label, 'w')
            for line in fid.readlines():
                line = line.strip()
                if len(line) < 1:
                    continue
                temp_list = line.split('-')
                temp_list = temp_list[1].split('+')
                mono_phone = temp_list[0]
                mid.write('{0}\n'.format(mono_phone))
            fid.close()
            mid.close()
        fid = open(self.mono_no_align_mlf, 'w')
        fid.write('#!MLF!#\n')
        fid.write('"*/*.lab" -> "' + self.mono_no_align_dir + '"\n')
        fid.close()

    def _postprocess(self):
        state_num = STATE_NUM
        mono_mlf = open(self.align_res_mlf, 'r')
        mono_mlf.readline()
        while True:
            line = mono_mlf.readline()
            line = line.strip()
            if len(line) < 1:
                break
            line = line.replace('"', '')
            file_base = os.path.basename(line)
            orig_label = open(os.path.join(self.full_dir, file_base), 'r')
            aligned_label = open(os.path.join(self.lab_dir, file_base), 'w')
            for lab in orig_label.readlines():
                lab = lab.strip().split()[2]
                for i in range(state_num):
                    line = mono_mlf.readline()
                    line = line.strip()
                    tmp_list = line.split()
                    aligned_label.write('{0} {1} {2}[{3}]\n'.format(tmp_list[0], tmp_list[1], lab, i+2))

            orig_label.close()
            aligned_label.close()
            line = mono_mlf.readline()
            line= line.strip()
            if line != '.':
                print('The two files are not matched!\n')
                sys.exit(1)
        mono_mlf.close()



if __name__ == '__main__':

    NIT_dir = sys.argv[1]
    lab_dir = sys.argv[2]
    wav_dir = os.path.join(NIT_dir, 'wav')
    work_dir = os.path.join(NIT_dir, 'label')
    full_dir = os.path.join(NIT_dir, 'full')

    aligner = ForcedAlignment(work_dir, NIT_dir, wav_dir, full_dir, lab_dir)
    aligner.prepare_training()
    # aligner.train_hmm(7, 32)
    aligner.align()
