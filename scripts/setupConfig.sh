INPUT=$1
OUTPUT=$2

cp -r configs/$INPUT configs/$OUTPUT
grep -rl "$INPUT" configs/$OUTPUT | xargs sed -i "s/$INPUT/$OUTPUT/g"

# cp -r configs/V45nano_$INPUT configs/V45nano_$OUTPUT
# grep -rl "$INPUT" configs/V45nano_$OUTPUT | xargs sed -i "s/_$INPUT/_$OUTPUT/g"
