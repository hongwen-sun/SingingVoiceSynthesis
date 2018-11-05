#!/bin/bash

echo "Step 2:"

global_config_file=conf/global_settings.cfg
source $global_config_file

NIT_dir=$1
wav_dir=${1}/wav
phone_align_dir=${1}/mono
work_dir=${1}/label #work directory for label files
state_label_dir=${work_dir}/label_state_align


echo "forced-alignment using HTK tools..."

sed -i s#'HTKDIR =.*'#'HTKDIR = "'$HTKDir'"'# ${WorkDir}/local/forced_alignment.py

python ${WorkDir}/local/forced_alignment.py $NIT_dir $state_label_dir

echo "Copying labels to duration and acoustic data directories..."

duration_data_dir=experiments/duration_model/data
acoustic_data_dir=experiments/acoustic_model/data

mkdir -p $duration_data_dir
mkdir -p $acoustic_data_dir

cp -r $state_label_dir $duration_data_dir 
cp -r $state_label_dir $acoustic_data_dir

ls $state_label_dir > $duration_data_dir/$FileIDList
ls $state_label_dir > $acoustic_data_dir/$FileIDList

sed -i 's/\.lab//g' $duration_data_dir/$FileIDList
sed -i 's/\.lab//g' $acoustic_data_dir/$FileIDList

#echo "done...!"
