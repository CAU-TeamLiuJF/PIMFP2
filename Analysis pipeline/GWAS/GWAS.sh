#!/usr/bin/bash



/storage2/liuz/software/GMAT-main/GMAT-main/gmat-1.01/uvlmm \
--bfile 1225finalmerged --data phenotype.txt \
--grm G --trait IMF --class breed,sex --covar weight --out IMF
