#!/bin/bash -e

function usage()
{
    echo " Usage : $0 [-f][-m <option>]"
}

voice=slt_arctic_demo
singing=true
architecture=DNN


while getopts m:sf parm ; do
case $parm in 
    m)
        echo "$OPTARG"
        architecture=$OPTARG
        ;;
    s)
        singing=false
        ;;
    f)
        voice=slt_arctic_full
        ;;
    *)
        usage
        echo "Invalid argument"
esac
done



### Step 1: setup directories and the training data files ###
./01_setup.sh ${voice}

### Step 2: prepare config files for acoustic, duration models and for synthesis ###
./02_prepare_conf_files.sh conf/global_settings.cfg $architecture singing

### Step 3: train duration model ###
./03_train_duration_model.sh conf/duration_${voice}.conf 

### Step 4: train acoustic model ###
./04_train_acoustic_model.sh conf/acoustic_${voice}.conf

### Step 5: synthesize speech ###
./05_run_merlin.sh conf/test_dur_synth_${voice}.conf conf/test_synth_${voice}.conf 

