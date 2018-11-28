#!/bin/bash


### argumants
glob_conf=$1
test_dir=$2

. conf/global_settings.cfg

### tools required
FESTDIR=${MerlinDir}/tools/build_fest/build/festival
frontend=${MerlinDir}/misc/scripts/frontend

txt_file=${test_dir}/lyric


python ${frontend}/utils/genScmFile.py \
                            ${txt_file} \
                            ${test_dir}/prompt-utt \
                            ${test_dir}/new_test_sentences.scm \
                            ${test_dir}/test_id_list.scp

### generate utt from scheme file
echo "generating utts from scheme file"
${FESTDIR}/bin/festival -b ${test_dir}/new_test_sentences.scm

### convert festival utt to lab
echo "converting festival utts to labels..."
${frontend}/festival_utt_to_lab/make_labels \
                            ${test_dir}/prompt-lab \
                            ${test_dir}/prompt-utt \
                            ${FESTDIR}/examples/dumpfeats \
                            ${frontend}/festival_utt_to_lab

### normalize lab for merlin with options: state_align or phone_align
echo "normalizing label files for merlin..."
python ${frontend}/utils/normalize_lab_for_merlin.py \
                            ${test_dir}/prompt-lab/full \
                            ${test_dir}/prompt-lab \
                            ${Labels} \
                            ${test_dir}/test_id_list.scp 0

### remove un-necessary files
rm -rf ${test_dir}/prompt-lab/{full,mono,tmp}

echo "Labels are ready in: ${test_dir}/prompt-lab !!"
