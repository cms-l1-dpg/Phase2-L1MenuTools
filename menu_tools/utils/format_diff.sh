OLDVERSION=$1
NEWVERSION=$2
COMPDIR=${3:-"comparisons"} 

if [[ -f outputs/$NEWVERSION/object_performance/objects.md && -f outputs/$OLDVERSION/object_performance/objects.md ]]; then
    # Objects
    mkdir -p outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/
    echo "# Diff of Object Definitions" | tee outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md

    if [[ -z $(git diff -U1000 --no-index outputs/$OLDVERSION/object_performance/objects.md outputs/$NEWVERSION/object_performance/objects.md) ]]; then
	echo "<b>Both versions are identical! Pasting for Reference.</b>"  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
	echo  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
	cat outputs/$NEWVERSION/object_performance/objects.md >> outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
    else
	echo "<b>Versions differ, look for the red and green lines!</b>"  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
	echo  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
	git diff -U1000 --no-index outputs/$OLDVERSION/object_performance/objects.md outputs/$NEWVERSION/object_performance/objects.md | \
	    sed '/^+++ /d;/^--- /d;/^@@ /d' | \
	    sed -E \
		-e 's/^(\+)(.*)/<pre><span style="color:green">\1\2<\/span><\/pre>/' \
		-e 's/^(-)(.*)/<pre><span style="color:red">\1\2<\/span><\/pre>/' \
		>> outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
    fi
    
    echo "Objects diff file is: outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md"
else
    echo "WARNING: One or both of the input object mds don't exist. Skipping."
    echo "Check on outputs/$NEWVERSION/object_performance/objects.md and outputs/$OLDVERSION/object_performance/objects.md"
fi

if [[ -f outputs/$OLDVERSION/rate_tables/triggers.md && -f outputs/$NEWVERSION/rate_tables/triggers.md ]]; then
    # Menus
    mkdir -p outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/
    echo "# Diff of Trigger Menus" | tee outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
    
    if [[ -z $(git diff -U1000 --no-index outputs/$OLDVERSION/rate_tables/triggers.md outputs/$NEWVERSION/rate_tables/triggers.md) ]]; then
	echo "<b>Both versions are identical! Pasting for Reference.</b>"  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
	echo  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
	cat outputs/$NEWVERSION/object_performance/objects.md >> outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
    else
	echo "<b>Versions differ, look for the red and green lines!</b>"  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
	echo  | tee -a outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
	git diff -U1000 --no-index outputs/$OLDVERSION/rate_tables/triggers.md outputs/$NEWVERSION/rate_tables/triggers.md | \
	    sed '/^+++ /d;/^--- /d;/^@@ /d' | \
	    sed -E \
		-e 's/^(\+)(.*)/<pre><span style="color:green">\1\2<\/span><\/pre>/' \
		-e 's/^(-)(.*)/<pre><span style="color:red">\1\2<\/span><\/pre>/' \
		>> outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
    fi
    
    echo "Menus diff file is: outputs/${COMPDIR}/${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md"
else
    echo "WARNING: One or both of the input trigger mds don't exist. Skipping."
    echo "Check on outputs/$OLDVERSION/rate_tables/triggers.md and outputs/$NEWVERSION/rate_tables/triggers.md"
fi

