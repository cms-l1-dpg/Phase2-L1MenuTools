INPUT=$1
OUTPUT=$2

OLDCMSSW=$3
NEWCMSSW=$4

if [[ -z $INPUT || -z $OUTPUT || -z $OLDCMSSW || -z $NEWCMSSW ]]; then
    echo "Missing an input argument, please check!"
else
    cp -r configs/$INPUT configs/$OUTPUT
    grep -rl "$INPUT" configs/$OUTPUT | xargs sed -i "s/$INPUT/$OUTPUT/g"
    sed -i "s/$OLDCMSSW/$NEWCMSSW/g" configs/$OUTPUT/caching.yaml

    echo "Caching config is here, please check: "
    cat configs/$OUTPUT/caching.yaml
fi

# cp -r configs/V45nano_$INPUT configs/V45nano_$OUTPUT
# grep -rl "$INPUT" configs/V45nano_$OUTPUT | xargs sed -i "s/_$INPUT/_$OUTPUT/g"

