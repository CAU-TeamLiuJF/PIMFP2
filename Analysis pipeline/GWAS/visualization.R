
library("CMplot")


A<-read.table("/public/home/08041/WORKSPACE/liuzhen2/IMF_GWAS_gmat/real/result/IMF_weight_003/picinput.txt",header=T)
CMplot(A,plot.type="q",main="Meat-IMF",
       signal.pch = 19,
       signal.cex = 0.8,
       signal.col="red",
       threshold.col = "black",
	   threshold.lty = 1,
       conf.int.col = NA,  
       height = 5,
       width = 5)



CMplot(A,main="Meat-IMF",
       plot.type="m", 
       LOG10 = TRUE,
       threshold = 1/N,  # N denotes the number of independent SNPs.
       threshold.lty = 1,  
       threshold.lwd = 1.5,  
       threshold.col = "black",  
       amplify = FALSE,  
       signal.cex = c(1.1, 0.8),
       chr.border = TRUE,
       signal.pch = c(19, 19),
       file = "pdf",  
       dpi = 50, 
       file.output = TRUE,  
       verbose = TRUE)
