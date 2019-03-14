export PATH=/opt/anaconda2/bin:$PATH
. /opt/anaconda2/etc/profile.d/conda.sh

unset PYTHONPATH

conda activate ml-suite
source $HOME/oss/ml-suite/overlaybins/setup.sh nimbix 
