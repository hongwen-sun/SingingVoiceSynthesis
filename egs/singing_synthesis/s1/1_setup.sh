#!/bin/bash


### Step 1: setup directories and the training data files ###
echo "Step 1:"

current_working_dir=$(pwd)
merlin_dir=$(dirname $(dirname $(dirname $current_working_dir)))
experiments_dir=${current_working_dir}/experiments

acoustic_dir=${experiments_dir}/acoustic_model
duration_dir=${experiments_dir}/duration_model
pitch_dir=${experiments_dir}/pitch_model
synthesis_dir=${experiments_dir}/test_synthesis

mkdir -p ${experiments_dir}
mkdir -p ${pitch_dir}
mkdir -p ${acoustic_dir}
mkdir -p ${duration_dir}


global_config_file=conf/global_settings.cfg

### default settings ###
echo "MerlinDir=${merlin_dir}" >  $global_config_file
echo "HTKDir=${merlin_dir}/tools/bin/htk" >> $global_config_file
echo "WorkDir=${current_working_dir}" >>  $global_config_file
echo "Labels=state_align" >> $global_config_file
echo "QuestionFile=questions-japanese-song.hed" >> $global_config_file
echo "Vocoder=WORLD" >> $global_config_file
echo "SamplingFreq=16000" >> $global_config_file

echo "FileIDList=file_id_list_demo.scp" >> $global_config_file
echo "Train=29" >> $global_config_file 
echo "Valid=1" >> $global_config_file 
echo "Test=1" >> $global_config_file 

echo "Merlin default voice settings configured in $global_config_file"
echo "setup done...!"
