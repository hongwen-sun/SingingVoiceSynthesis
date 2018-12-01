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
        echo "-m is triggered"
        echo "$OPTARG"
        architecture=$OPTARG
        ;;
    s)
        echo "-t is triggered"
        singing=false
        ;;
    f)
        echo "-f is triggered"
        voice=slt_arctic_full
        ;;
    *)
        usage
        echo "Invalid argument"
esac
done



### Step 1: setup directories and the training data files ###
#./01_setup.sh slt_arctic_demo
#./01_setup.sh slt_arctic_full
./01_setup.sh ${voice}

### Step 2: prepare config files for acoustic, duration models and for synthesis ###
./02_prepare_conf_files.sh conf/global_settings.cfg $architecture singing

### Step 3: train duration model ###
#./03_train_duration_model.sh conf/duration_slt_arctic_demo.conf
#./03_train_duration_model.sh conf/duration_slt_arctic_full.conf 
./03_train_duration_model.sh conf/duration_${voice}.conf 

### Step 4: train acoustic model ###
#./04_train_acoustic_model.sh conf/acoustic_slt_arctic_demo.conf
#./04_train_acoustic_model.sh conf/acoustic_slt_arctic_full.conf
./04_train_acoustic_model.sh conf/acoustic_${voice}.conf

### Step 5: synthesize speech ###
./05_run_merlin.sh conf/test_dur_synth_${voice}.conf conf/test_synth_${voice}.conf 
#./05_run_merlin.sh conf/test_dur_synth_slt_arctic_full.conf conf/test_synth_slt_arctic_full.conf 

