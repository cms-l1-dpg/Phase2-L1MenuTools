# Copy one caching config to a new sub-version within the same config directory:
#   configs/<MAJOR>/cache_objects/caching_<OLD>.yaml -> caching_<NEW>.yaml
# The top-level version key gets its trailing _<OLD> swapped for _<NEW> (falls back to
# <MAJOR>_<NEW> if the key doesn't end in _<OLD>), and if OLDCMSSW/NEWCMSSW are given,
# they are swapped on the ntuple_path lines only.
#
# Usage: . scripts/setupCache.sh MAJOR OLD NEW [OLDCMSSW NEWCMSSW]
#   e.g. . scripts/setupCache.sh V50nano 170pre5 170pre5_SC8mass 170pre5 170pre5_SC8mass

MAJOR=$1
OLD=$2
NEW=$3
OLDCMSSW=$4
NEWCMSSW=$5

DIR=configs/$MAJOR/cache_objects
SRC=$DIR/caching_$OLD.yaml
DST=$DIR/caching_$NEW.yaml

if [[ -z $MAJOR || -z $OLD || -z $NEW ]]; then
    echo "Usage: . scripts/setupCache.sh MAJOR OLD NEW [OLDCMSSW NEWCMSSW]"
elif [[ -n $OLDCMSSW && -z $NEWCMSSW ]]; then
    echo "OLDCMSSW given without NEWCMSSW, please check!"
elif [[ ! -f $SRC ]]; then
    echo "$SRC does not exist, please check!"
elif [[ -e $DST ]]; then
    echo "$DST already exists, not overwriting"
else
    OLDKEY=$(head -1 "$SRC" | sed 's/:.*//')
    if [[ $OLDKEY == *_$OLD ]]; then
        NEWKEY=${OLDKEY%_$OLD}_$NEW
    else
        NEWKEY=${MAJOR}_$NEW
        echo "Warning: key $OLDKEY does not end in _$OLD, using $NEWKEY"
    fi

    cp "$SRC" "$DST"
    sed -i "1s/^$OLDKEY:/$NEWKEY:/" "$DST"
    if [[ -n $OLDCMSSW ]]; then
        sed -i "/ntuple_path:/s/$OLDCMSSW/$NEWCMSSW/g" "$DST"
    fi

    echo "Caching config is here, please check: $DST"
    grep -E "^[^ #]|ntuple_path" "$DST"
fi
