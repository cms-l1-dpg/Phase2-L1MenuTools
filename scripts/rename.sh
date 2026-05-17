# OLDVERSION=V38nano_DT12x
# NEWVERSION=V38nano_DT12x_Oct24
OLDVERSION=$1
NEWVERSION=$2

# HEADDIR=cache
HEADDIR=outputs


if [ -d "$HEADDIR/$OLDVERSION" ]; then
    mv $HEADDIR/$OLDVERSION $HEADDIR/$NEWVERSION

    cd $HEADDIR/$NEWVERSION

    # Filenames
    for file in $(find -name "*$OLDVERSION*"); do
	echo Oldname: $file
	echo Newname: ${file/$OLDVERSION/$NEWVERSION}
	mv $file ${file/$OLDVERSION/$NEWVERSION}
    done

    echo "Files renamed, now checking in files"
    # Text within files
    grep -rl $OLDVERSION | xargs sed -i "s/$OLDVERSION/$NEWVERSION/g"

    cd -
else
    echo "ERROR: Old version $HEADDIR/$OLDVERSION doesnt exist, please check"
fi
