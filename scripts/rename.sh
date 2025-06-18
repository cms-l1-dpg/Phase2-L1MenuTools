OLDVERSION=V38nano_DT12x
NEWVERSION=V38nano_DT12x_Oct24

cd $NEWVERSION

# Filenames
for file in $(find -name *$OLDVERSION*); do
    echo Oldname: $file
    echo Newname: ${file/$OLDVERSION/$NEWVERSION}
    mv $file ${file/$OLDVERSION/$NEWVERSION}
done

# Text within files
grep -rl $OLDVERSION --exclude rename.sh | xargs sed -i "s/$OLDVERSION/$NEWVERSION/g"

cd -
