export CONDA2PATH=$HOME/anaconda2
export MLSUITE_ROOT=$HOME/oss/ml-suite

unset PYTHONPATH
export PATH=$CONDA2PATH/bin:$PATH
source $CONDA2PATH/etc/profile.d/conda.sh

conda activate ml-suite
source $HOME/oss/ml-suite/overlaybins/setup.sh 1525
