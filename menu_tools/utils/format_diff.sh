OLDVERSION=$1
NEWVERSION=$2
COMPDIR=$3 

# Objects
echo "# Diff of Object Definitions" | tee outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
echo "<b>Note: If no green or red lines appear, both sets of configs are identical</b>"  | tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md
echo  | tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md

git diff -U1000 --no-index outputs/$OLDVERSION/object_performance/objects.md outputs/$NEWVERSION/object_performance/objects.md | \
sed '/^+++ /d;/^--- /d;/^@@ /d' | \
sed -E \
  -e 's/^(\+)(.*)/<pre><span style="color:green">\1\2<\/span><\/pre>/' \
  -e 's/^(-)(.*)/<pre><span style="color:red">\1\2<\/span><\/pre>/' | \
tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md

echo "Objects diff file is: outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/object_performance/objects.md"


# Menus
echo "# Diff of Trigger Menus" | tee outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
echo "<b>Note: If no green or red lines appear, both sets of configs are identical</b>"  | tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md
echo  | tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md

git diff -U1000 --no-index outputs/$OLDVERSION/rate_tables/triggers.md outputs/$NEWVERSION/rate_tables/triggers.md | \
sed '/^+++ /d;/^--- /d;/^@@ /d' | \
sed -E \
  -e 's/^(\+)(.*)/<pre><span style="color:green">\1\2<\/span><\/pre>/' \
  -e 's/^(-)(.*)/<pre><span style="color:red">\1\2<\/span><\/pre>/' | \
tee -a outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md

echo "Menus diff file is: outputs/comparisons/${COMPDIR}${NEWVERSION}vs${OLDVERSION}/rate_tables/triggers.md"
