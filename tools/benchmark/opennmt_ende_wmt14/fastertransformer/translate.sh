#!/bin/bash

SOURCE_FILE=$2
OUTPUT_FILE=$3

BATCH_SIZE=32
BEAM_SIZE=4
FP16=${FP16:-0}
if [ $FP16 = "1" ]; then
    DATA_TYPE="fp16"
else
    DATA_TYPE="fp32"
fi

./bin/decoding_gemm $BATCH_SIZE $BEAM_SIZE 8 64 31538 100 512 $FP16
python3 pytorch/run_translation.py --model_path /workspace/averaged-10-epoch.pt --input_file $SOURCE_FILE --output_file $OUTPUT_FILE --batch_size $BATCH_SIZE --beam_size $BEAM_SIZE --model_type decoding_ext --data_type $DATA_TYPE
