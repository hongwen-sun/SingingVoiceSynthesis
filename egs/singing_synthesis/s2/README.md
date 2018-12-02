# Singing Synthesis by Hard-coding Pitch and Duration Trained with SLT Arctic

## Set up
Clone repository and install tools:
```
git clone https://github.com/YongliangHe/SingingVoiceSynthesis
cd SingingVoiceSynthesis
./tools/compile_tools.sh
./tools/compile_htk.sh
./tools/compile_other_speech_tools.sh
```

## Train models and run synthesizer
```
cd egs/singing_synthesis/s2
./run.sh
```
Generated samples will be placed in experiments/slt_arctic_demo/test_synthesis/wav/

## Specify network architectures and traning set (full or demo)
Run script with options. For example, the commond below will train LSTMs with the whole arctic data:
```
./run.sh -f -m LSTM
```

## Edit score
The synthesizer generate samples according to a music score (placed in the working directory named "score"), which is basically a list of pitch-duration pairs at "syllabel level"

## Demoes
Demo samples could be found at demo_samples dir
