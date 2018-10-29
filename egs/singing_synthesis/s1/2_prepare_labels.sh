#!/bin/bash

global_config_file=conf/global_settings.cfg
source $global_config_file

#if test "$#" -ne 3; then
    #echo "################################"
    #echo "Usage:"
    #echo "./02_prepare_labels.sh <path_to_wav_dir> <path_to_text_dir> <path_to_labels_dir>"
    #echo ""
    #echo "default path to wav dir(Input): database/wav"
    #echo "default path to txt dir(Input): database/txt"
    #echo "default path to lab dir(Output): database/labels"
    #echo "################################"
    #exit 1
#fi

wav_dir=$1
phone_align_dir=$2
work_dir=$3 #work directory for label files
state_label_dir=${work_dir}/state_align_label








#./local/run_state_aligner.sh $wav_dir $phone_align_dir $state_label_dir $global_config_file 


echo "forced-alignment using HTK tools..."
echo $wav_dir

sed -i s#'HTKDIR =.*'#'HTKDIR = "'$HTKDir'"'# ${WorkDir}/local/forced_alignment.py
sed -i s#'work_dir =.*'#'work_dir = "'$work_dir'"'# ${WorkDir}/local/forced_alignment.py
sed -i s#'wav_dir =.*'#'wav_dir = "'$wav_dir'"'# ${WorkDir}/local/forced_alignment.py

python ${WorkDir}/local/forced_alignment.py $work_dir $wav_dir

#if [ "$copy" = true ]; then
    #echo "Copying labels to duration and acoustic data directories..."
    
    #duration_data_dir=experiments/${Voice}/duration_model/data
    #acoustic_data_dir=experiments/${Voice}/acoustic_model/data
    
    #cp -r $lab_dir/label_$Labels $duration_data_dir 
    #cp -r $lab_dir/label_$Labels $acoustic_data_dir
    
    #ls $lab_dir/label_$Labels > $duration_data_dir/$FileIDList
    #ls $lab_dir/label_$Labels > $acoustic_data_dir/$FileIDList
    
    #sed -i 's/\.lab//g' $duration_data_dir/$FileIDList
    #sed -i 's/\.lab//g' $acoustic_data_dir/$FileIDList
    
    #echo "done...!"
#fi
