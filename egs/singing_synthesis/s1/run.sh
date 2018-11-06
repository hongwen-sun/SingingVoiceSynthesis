#!/bin/bash -e

#if test "$#" -ne 0; then
    #echo "Usage: ./run_demo.sh"
    #exit 1
#fi
source ./conf/global_settings.cfg

### Step 1: setup directories and the training data files ###
./1_setup.sh

### Step 2: prepare state level label files
./2_prepare_labels.sh ${WorkDir}/NIT

### Step 3: extract acoustic features
./3_prepare_acoustic_features.sh ${WorkDir}/NIT/wav2 ${WorkDir}/NIT/feats

### Step 4: 
./4_prepare_conf_files.sh conf/global_settings.cfg

### Step 5:
./5_train_duration_model.sh conf/duration.conf

### Step 6:
./6_train_acoustic_model.sh conf/acoustic.conf

### Step 7:
./7_synthesize.sh conf/test_dur_synth.conf conf/test_synth.conf

