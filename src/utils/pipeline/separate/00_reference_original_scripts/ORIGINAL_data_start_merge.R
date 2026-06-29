######
#BOF study WO EMA (PREPROCESSING)
#last update: 15/04/2022
######

#set wd
setwd("~/E-Health/PROJECT/BOF project/STUDIE 1/Analyses/Data/Raw data")

#libraries
library(foreign)
library(eeptools)
library(score)
library(MASS)
library(xlsx)

#read-in data
data <- read.spss("2022 04 05 Data begin studie WO EMA.sav", to.data.frame=TRUE, trim.factor.names=TRUE, stringsAsFactors=FALSE)
str(data)

data$token <- trimws(data$token)
#exclude participants 
#data <- data[which(data$token != "wo0026569" & data$token != "wo0067892" & data$token != "wo0276757" & data$token != "wo0327640" & data$token != "wo0193167"),]
#remark: wo19 no valid IPAQ data. Can be included for other analyses

data <- data[which(data$token != "wo0026569" & data$token != "wo0067892"),]

#recode variables
data$token <- factor(data$token)
data$Leeftijd <- as.POSIXct(data$Leeftijd, origin="1582-10-14", tz="GMT")
data$Leeftijd <- as.Date(as.POSIXct(data$Leeftijd))
data$submitdate <- as.POSIXct(data$submitdate, origin="1582-10-14", tz="GMT")
data$submitdate <- as.Date(as.POSIXct(data$submitdate))
data$Leeftijd2 <- floor(age_calc(data$Leeftijd,data$submitdate, units = "years"))
data$GCPS3_GCPS3 <- as.numeric(data$GCPS3_GCPS3)-1
data$GCPS4_GCPS4 <- as.numeric(data$GCPS4_GCPS4)-1
data$GCPS5_GCPS5 <- as.numeric(data$GCPS5_GCPS5)-1
data$POAMP_1 <- as.numeric(data$POAMP_1)-1
data$POAMP_2 <- as.numeric(data$POAMP_2)-1
data$POAMP_3 <- as.numeric(data$POAMP_3)-1
data$POAMP_4 <- as.numeric(data$POAMP_4)-1
data$POAMP_5 <- as.numeric(data$POAMP_5)-1
data$POAMP_6 <- as.numeric(data$POAMP_6)-1
data$POAMP_7 <- as.numeric(data$POAMP_7)-1
data$POAMP_8 <- as.numeric(data$POAMP_8)-1
data$POAMP_9 <- as.numeric(data$POAMP_9)-1
data$POAMP_10 <- as.numeric(data$POAMP_10)-1
data$POAMP_11 <- as.numeric(data$POAMP_11)-1
data$POAMP_12 <- as.numeric(data$POAMP_12)-1
data$POAMP_13 <- as.numeric(data$POAMP_13)-1
data$POAMP_14 <- as.numeric(data$POAMP_14)-1
data$POAMP_15 <- as.numeric(data$POAMP_15)-1
data$POAMP_16 <- as.numeric(data$POAMP_16)-1
data$POAMP_17 <- as.numeric(data$POAMP_17)-1
data$POAMP_18 <- as.numeric(data$POAMP_18)-1
data$POAMP_19 <- as.numeric(data$POAMP_19)-1
data$POAMP_20 <- as.numeric(data$POAMP_20)-1
data$POAMP_21 <- as.numeric(data$POAMP_21)-1
data$POAMP_22 <- as.numeric(data$POAMP_22)-1
data$POAMP_23 <- as.numeric(data$POAMP_23)-1
data$POAMP_24 <- as.numeric(data$POAMP_24)-1
data$POAMP_25 <- as.numeric(data$POAMP_25)-1
data$POAMP_26 <- as.numeric(data$POAMP_26)-1
data$POAMP_27 <- as.numeric(data$POAMP_27)-1
data$POAMP_28 <- as.numeric(data$POAMP_28)-1
data$POAMP_29 <- as.numeric(data$POAMP_29)-1
data$POAMP_30 <- as.numeric(data$POAMP_30)-1
data$TSK_1 <- as.numeric(data$TSK_1)
data$TSK_2 <- as.numeric(data$TSK_2)
data$TSK_3 <- as.numeric(data$TSK_3)
data$TSK_4 <- as.numeric(data$TSK_4)
data$TSK_5 <- as.numeric(data$TSK_5)
data$TSK_6 <- as.numeric(data$TSK_6)
data$TSK_7 <- as.numeric(data$TSK_7)
data$TSK_8 <- as.numeric(data$TSK_8)
data$TSK_9 <- as.numeric(data$TSK_9)
data$TSK_10 <- as.numeric(data$TSK_10)
data$TSK_11 <- as.numeric(data$TSK_11)
data$TSK_12 <- as.numeric(data$TSK_12)
data$TSK_13 <- as.numeric(data$TSK_13)
data$TSK_14 <- as.numeric(data$TSK_14)
data$TSK_15 <- as.numeric(data$TSK_15)
data$TSK_16 <- as.numeric(data$TSK_16)
data$TSK_17 <- as.numeric(data$TSK_17)
data$pijninterferentie_1 <- as.numeric(data$pijninterferentie_1)
data$pijninterferentie_2 <- as.numeric(data$pijninterferentie_2)
data$pijninterferentie_3 <- as.numeric(data$pijninterferentie_3)
data$pijninterferentie_4 <- as.numeric(data$pijninterferentie_4)
data$pijninterferentie_5 <- as.numeric(data$pijninterferentie_5)
data$pijninterferentie_6 <- as.numeric(data$pijninterferentie_6)
data$pijninterferentie_7 <- as.numeric(data$pijninterferentie_7)
data$pijninterferentie_8 <- as.numeric(data$pijninterferentie_8)

data$Motivatie_MOT1 <- as.numeric(data$Motivatie_MOT1)
data$Motivatie_MOT2 <- as.numeric(data$Motivatie_MOT2)
data$Motivatie_MOT3 <- as.numeric(data$Motivatie_MOT3)
data$Motivatie_MOT4 <- as.numeric(data$Motivatie_MOT4)
data$Motivatie_MOT5 <- as.numeric(data$Motivatie_MOT5)

data$EigenEff_EE1 <- as.numeric(data$EigenEff_EE1)
data$EigenEff_EE2 <- as.numeric(data$EigenEff_EE2)
data$EigenEff_EE3 <- as.numeric(data$EigenEff_EE3)
data$EigenEff_EE4 <- as.numeric(data$EigenEff_EE4)
data$EigenEff_EE5 <- as.numeric(data$EigenEff_EE5)
data$EigenEff_EE6 <- as.numeric(data$EigenEff_EE6)

data$OE_OE1 <- as.numeric(data$OE_OE1)
data$OE_OE2 <- as.numeric(data$OE_OE2)
data$OE_OE3 <- as.numeric(data$OE_OE3)
data$OE_OE4 <- as.numeric(data$OE_OE4)
data$OE_OE5 <- as.numeric(data$OE_OE5)
data$OE_OE6 <- as.numeric(data$OE_OE6)
data$OE_OE7 <- as.numeric(data$OE_OE7)
data$OE_OE8 <- as.numeric(data$OE_OE8)

data$RP_RP1 <- as.numeric(data$RP_RP1)
data$RP_RP2 <- as.numeric(data$RP_RP2)
data$RP_RP3 <- as.numeric(data$RP_RP3)
data$RP_RP4 <- as.numeric(data$RP_RP4)
data$RP_RP5 <- as.numeric(data$RP_RP5)

data$ActiePlanning_AP1 <- as.numeric(data$ActiePlanning_AP1)
data$ActiePlanning_AP2 <- as.numeric(data$ActiePlanning_AP2)
data$ActiePlanning_AP3 <- as.numeric(data$ActiePlanning_AP3)

data$CopingPlanning_CP1 <- as.numeric(data$CopingPlanning_CP1)
data$CopingPlanning_CP2 <- as.numeric(data$CopingPlanning_CP2)

data$ZelfMonitoring_SM1 <- as.numeric(data$ZelfMonitoring_SM1)
data$ZelfMonitoring_SM2 <- as.numeric(data$ZelfMonitoring_SM2)
data$ZelfMonitoring_SM3 <- as.numeric(data$ZelfMonitoring_SM3)


#one value of 0 for age -> set to NA
data$Leeftijd2 <- ifelse(data$Leeftijd2 == 0,NA,data$Leeftijd2)

#univariate analysis of variables of interest
table(data$Geslacht) #36 vrouwen
table(data$Handigheid) #1 linkshandig, 35 rechtshandig
mean(data$Leeftijd2, na.rm=TRUE)
sd(data$Leeftijd2, na.rm=TRUE)
hist(data$Leeftijd2)
range(data$Leeftijd2, na.rm=TRUE) #21 tot 74 jaar
table(data$Opleiding)

barplot(table(data$Opleiding), legend=TRUE, col=c("blue", "green", "red", "yellow", "purple", "orange"),
        args.legend=list(x=8, y=-2,ncol=2))
pie(prop.table(table(data$Opleiding)), labels=(prop.table(table(data$Opleiding))), col=c("blue", "green", "red", "yellow", "purple", "orange"))
legend("bottomleft", c("Lager onderwijs (tot 12 jaar)","Lager secundair onderwijs (tot 15 jaar)",
                       "Hoger secundair onderwijs (tot 18 jaar)","Hoger beroepsonderwijs",
                       "Hoger niet-universitair onderwijs", "Hoger universitair onderwijs"), cex = 0.6,
       fill = c("blue", "green", "red", "yellow", "purple", "orange"))

#calculate BMI
data$BMI <- data$Gewicht/((data$Grootte/100)^2)
hist(data$BMI)
mean(data$BMI)
sd(data$BMI)

table(data$Kinderen)
table(data$ThuiswonendKinderen)

#create one variable that indicates whether participants have children living at home
data$ThuiswonendKinderen2 <- ifelse(data$Kinderen == "Geen",2, data$ThuiswonendKinderen)
table(data$ThuiswonendKinderen2)

data$ThuiswonendKinderen2 <- factor(data$ThuiswonendKinderen2,
                                    levels=c(1,2),
                                    labels=c("Ja", "Nee"))

#create variable at work versus not at work
data$Werk <- ifelse(data$Werk_2=="Ja", "Betaald werk",
                    ifelse(data$Werk_8=="Ja" |data$Werk_9=="Ja", "Invaliditeitsuitkering", "Andere"))

prop.table(table(data$Werk))
table(data$BurgerlijkeStaat)

#Graded Chronic Pain Scale
data$GCPS_PEG <- data$GCPS3_GCPS3+data$GCPS4_GCPS4+data$GCPS5_GCPS5

data$GCPS_Grade <- ifelse(data$GCPS1_GCPS1 == "Nooit" | data$GCPS1_GCPS1 == "Enkele dagen", 0,
                          ifelse(data$GCPS2_GCPS2 == "De meeste dagen" | data$GCPS2_GCPS2 == "Elke dag", 3,
                                 ifelse(data$GCPS_PEG <12,1,2)))
prop.table(table(data$GCPS_Grade))

#POAM-P
data$POAMP_Avoidance <- data$POAMP_1 + data$POAMP_6 + data$POAMP_8 + data$POAMP_11 + data$POAMP_13 + data$POAMP_16 +
  data$POAMP_19 + data$POAMP_22 + data$POAMP_25 + data$POAMP_28

data$POAMP_Overdoing <- data$POAMP_2 + data$POAMP_4 + data$POAMP_7 + data$POAMP_10 + data$POAMP_15 +
  data$POAMP_18 + data$POAMP_20 + data$POAMP_23 + data$POAMP_26 + data$POAMP_30

data$POAMP_Pacing <- data$POAMP_3 + data$POAMP_5 + data$POAMP_9 + data$POAMP_12 + data$POAMP_14 + 
  data$POAMP_17 + data$POAMP_21 + data$POAMP_24 + data$POAMP_27 + data$POAMP_29

#Pain interference (PROMIS)
data$pijninterferentie_sum <- data$pijninterferentie_1+data$pijninterferentie_2+data$pijninterferentie_3+data$pijninterferentie_4+
  data$pijninterferentie_5+data$pijninterferentie_6+data$pijninterferentie_7+data$pijninterferentie_8
data$pijninterferentie_Tscore <- ifelse(data$pijninterferentie_sum==8,40.7,
                                        ifelse(data$pijninterferentie_sum==9,47.9,
                                               ifelse(data$pijninterferentie_sum==10,49.9,
                                                      ifelse(data$pijninterferentie_sum==11,51.2,
                                                             ifelse(data$pijninterferentie_sum==12,52.3,
                                                                    ifelse(data$pijninterferentie_sum==13,53.2,
                                                                           ifelse(data$pijninterferentie_sum==14,54.1,
                                                                                  ifelse(data$pijninterferentie_sum==15,55,
                                                                                         ifelse(data$pijninterferentie_sum==16,55.8,
                                                                                                ifelse(data$pijninterferentie_sum==17,56.6,
                                                                                                       ifelse(data$pijninterferentie_sum==18,57.4,
                                                                                                              ifelse(data$pijninterferentie_sum==19,58.1,
                                                                                                                     ifelse(data$pijninterferentie_sum==20,58.8,
                                                                                                                            ifelse(data$pijninterferentie_sum==21,59.5,
                                                                                                                                   ifelse(data$pijninterferentie_sum==22,60.2,
                                                                                                                                          ifelse(data$pijninterferentie_sum==23,60.8,
                                                                                                                                                 ifelse(data$pijninterferentie_sum==24,61.5,
                                                                                                                                                        ifelse(data$pijninterferentie_sum==25,62.1,
                                                                                                                                                               ifelse(data$pijninterferentie_sum==26,62.8,
                                                                                                                                                                      ifelse(data$pijninterferentie_sum==27,63.5,
                                                                                                                                                                             ifelse(data$pijninterferentie_sum==28,64.1,
                                                                                                                                                                                    ifelse(data$pijninterferentie_sum==29,64.8,
                                                                                                                                                                                           ifelse(data$pijninterferentie_sum==30,65.5,
                                                                                                                                                                                                  ifelse(data$pijninterferentie_sum==31,66.2,
                                                                                                                                                                                                         ifelse(data$pijninterferentie_sum==32,66.9,
                                                                                                                                                                                                                ifelse(data$pijninterferentie_sum==33,67.7,
                                                                                                                                                                                                                       ifelse(data$pijninterferentie_sum==34,68.4,
                                                                                                                                                                                                                              ifelse(data$pijninterferentie_sum==35,69.2,
                                                                                                                                                                                                                                     ifelse(data$pijninterferentie_sum==36,70.1,
                                                                                                                                                                                                                                            ifelse(data$pijninterferentie_sum==37,71,
                                                                                                                                                                                                                                                   ifelse(data$pijninterferentie_sum==38,72.1,
                                                                                                                                                                                                                                                          ifelse(data$pijninterferentie_sum==39,73.5,
                                                                                                                                                                                                                                                                 ifelse(data$pijninterferentie_sum==40,77,NA)))))))))))))))))))))))))))))))))

#TSK
data$TSK_4_rev <- ifelse(data$TSK_4==4,1,
                         ifelse(data$TSK_4==3,2,
                                ifelse(data$TSK_4==2,3,4)))
data$TSK_8_rev <- ifelse(data$TSK_8==4,1,
                         ifelse(data$TSK_8==3,2,
                                ifelse(data$TSK_8==2,3,4)))
data$TSK_12_rev <- ifelse(data$TSK_12==4,1,
                          ifelse(data$TSK_12==3,2,
                                 ifelse(data$TSK_12==2,3,4)))
data$TSK_16_rev <- ifelse(data$TSK_16==4,1,
                          ifelse(data$TSK_16==3,2,
                                 ifelse(data$TSK_16==2,3,4)))

data$TSK_sum <- data$TSK_4_rev + data$TSK_8_rev + data$TSK_12_rev + data$TSK_16_rev + data$TSK_1 + data$TSK_2 + data$TSK_3 + data$TSK_5 + 
  data$TSK_6 + data$TSK_7 + data$TSK_9 + data$TSK_10 + data$TSK_11 + data$TSK_13 + data$TSK_14 + data$TSK_15 + data$TSK_17 
hist(data$TSK_sum)


#Determinants
#Motivation
#extrinsic motivation
data$extr_mot <- (data$Motivatie_MOT1+data$Motivatie_MOT2)/2
data$intr_mot <- (data$Motivatie_MOT3+data$Motivatie_MOT4+data$Motivatie_MOT5)/3

hist(data$extr_mot)
hist(data$intr_mot)

#self-efficacy
data$SE <- (data$EigenEff_EE1 + data$EigenEff_EE2 + data$EigenEff_EE3 + data$EigenEff_EE4 + data$EigenEff_EE5 + data$EigenEff_EE6)/6
hist(data$SE)


#Outcome expectancies
#reverse coding OE7en 0E8
data$OE_OE7_rev <- ifelse(data$OE_OE7 == 1,5,
                          ifelse(data$OE_OE7 == 2,4,
                                 ifelse(data$OE_OE7 == 4,2,
                                        ifelse(data$OE_OE7==5,1,data$OE_OE7))))

data$OE_OE8_rev <- ifelse(data$OE_OE8 == 1,5,
                          ifelse(data$OE_OE8 == 2,4,
                                 ifelse(data$OE_OE8 == 4,2,
                                        ifelse(data$OE_OE8==5,1,data$OE_OE8))))

data$OE <- (data$OE_OE1 + data$OE_OE2 + data$OE_OE3 + data$OE_OE4 + 
              data$OE_OE5 + data$OE_OE6 + data$OE_OE7_rev + data$OE_OE8_rev)/8
hist(data$OE)

#Risk perception
data$RP <- (data$RP_RP1+data$RP_RP2+data$RP_RP3+data$RP_RP4+data$RP_RP5)/5
hist(data$RP)

#Action planning
#AP3 reverse coding
data$ActiePlanning_AP3_rev <- ifelse(data$ActiePlanning_AP3 == 1,5,
                                     ifelse(data$ActiePlanning_AP3 == 2,4,
                                            ifelse(data$ActiePlanning_AP3 == 4,2,
                                                   ifelse(data$ActiePlanning_AP3==5,1,data$ActiePlanning_AP3))))

data$AP <- (data$ActiePlanning_AP1+data$ActiePlanning_AP2+data$ActiePlanning_AP3_rev)/3
hist(data$AP)

#Coping planning
data$CP <- (data$CopingPlanning_CP1+data$CopingPlanning_CP2)/2
hist(data$CP)

#self-monitoring
data$SM <- (data$ZelfMonitoring_SM1+data$ZelfMonitoring_SM2+data$ZelfMonitoring_SM3)/3
hist(data$SM)

#stadium
table(data$Stadium)
prop.table(table(data$Stadium))
barplot(table(data$Stadium), legend=TRUE, col=c("blue", "green", "red", "yellow", "purple", "black"),
        args.legend=list(x=8, y=-2,ncol=2))
pie(prop.table(table(data$Stadium)), labels=round(prop.table(table(data$Stadium)),2), col=c("red", "pink", "orange", "yellow","lightgreen", "darkgreen"))
legend("bottomleft", c("Nee, en ik ben niet van plan hiermee te starten","Nee, maar ik overweeg het",
                       "Nee, maar ik heb de intentie om hiermee te beginnen","Nee, ik heb de intentie om dit te doen, maar het lukt niet",
                       "Ja, ik doe dit al sinds korte tijd", "Ja, ik doet dit al sinds lange tijd"), cex = 0.6,
       fill = c("red", "pink","orange", "yellow","lightgreen", "darkgreen"))

#IPAQ
#categorize individuals in low, moderate or high (see excel file)
dataIPAQ <- data[,c(3,12,194:204)]
head(dataIPAQ)

colnames(dataIPAQ) <- c("ID", "weight", "VigDays", "VigHours", "VigMin", "ModDays", "ModHours", 
                        "ModMin", "WalkDays", "WalkHours", "WalkMin", "SitHours", "SitMin")

str(dataIPAQ)

dataIPAQ$VigDays <- as.numeric(dataIPAQ$VigDays)-1
dataIPAQ$ModDays <- as.numeric(dataIPAQ$ModDays)-1
dataIPAQ$WalkDays <- as.numeric(dataIPAQ$WalkDays)-1

dataIPAQ$VigHours <- ifelse(is.na(dataIPAQ$VigHours),0,dataIPAQ$VigHours)
dataIPAQ$VigMin <- ifelse(is.na(dataIPAQ$VigMin),0,dataIPAQ$VigMin)
dataIPAQ$ModHours <- ifelse(is.na(dataIPAQ$ModHours),0,dataIPAQ$ModHours)
dataIPAQ$ModMin <- ifelse(is.na(dataIPAQ$ModMin),0,dataIPAQ$ModMin)
dataIPAQ$WalkHours <- ifelse(is.na(dataIPAQ$WalkHours),0,dataIPAQ$WalkHours)
dataIPAQ$WalkMin <- ifelse(is.na(dataIPAQ$WalkMin),0,dataIPAQ$WalkMin)


#calculate MEt values
dataIPAQ$WalkingMET <- 3.3*dataIPAQ$WalkMin*dataIPAQ$WalkDays
dataIPAQ$ModMET <- 4.0*dataIPAQ$ModMin*dataIPAQ$ModDays
dataIPAQ$VigMET <- 8.0*dataIPAQ$VigMin*dataIPAQ$VigDays

dataIPAQ$totalMET <- dataIPAQ$WalkingMET+dataIPAQ$ModMET+dataIPAQ$VigMET

#exclude participant wo19
dataIPAQ$totalMET <- ifelse(dataIPAQ$totalMET >5000,NA,dataIPAQ$totalMET) 

#dataIPAQ <- ipaq(ipaqdata=dataIPAQ)

#data$IPAQcat <- dataIPAQ$pacat
data$IPAQmet <- dataIPAQ$totalMET

hist(data$IPAQmet)
#table(data$IPAQcat)

# pie(prop.table(table(data$IPAQcat)), labels=(prop.table(table(data$IPAQcat))), col=c("green", "orange", "red"))
# legend("bottomleft", c("High", "Low", "Moderate"), cex = 0.6,
#        fill = c("green", "orange", "red"))



#read-in SEMA and Axivity data
setwd("~/E-Health/PROJECT/BOF project/STUDIE 1/Analyses/Data")
data_Ax <- read.xlsx("2022 08 23 walkon_emastudie_merged_triggerlevel (extra triggers removed).xlsx", sheetIndex=1)


#merge data start study with SEMA3 and Axivity data
data_all <- merge(data, data_Ax, by="token",all=TRUE)

#Export all data

# install.packages("openxlsx")
library(openxlsx)

write.xlsx(data_all, file = "2026 04 20 WO_EMA_alldata.xlsx", sheetName = "Sheet1")

