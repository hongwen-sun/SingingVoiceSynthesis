
MerlinDir=/home/yongliang/third_party/merlin
FESTDIR=${MerlinDir}/tools/build_fest/build/festival
frontend=${MerlinDir}/misc/scripts/frontend
testDir=debug/
Labels=state_align

txt_dir=${testDir}/txt



python ${frontend}/utils/genScmFile.py \
                            ${txt_dir} \
                            ${testDir}/\
                            ${testDir}/new_test_sentences.scm \
                            ${testDir}/test_id_list.scp 

echo "generating utts from scheme file"
${FESTDIR}/bin/festival -b ${testDir}/new_test_sentences.scm 


echo "converting festival utts to labels..."
${frontend}/festival_utt_to_lab/make_labels \
                            ${testDir}/ \
                            ${testDir}/ \
                            ${FESTDIR}/examples/dumpfeats \
                            ${frontend}/festival_utt_to_lab

echo "normalizing label files for merlin..."
echo "${testDir}/full"
echo "${testDir}"
echo "${Labels}"
echo "${testDir}/test_id_list.scp"
python ${frontend}/utils/normalize_lab_for_merlin.py \
                            ${testDir}/full \
                            ${testDir}/ \
                            ${Labels} \
                            ${testDir}/test_id_list.scp
