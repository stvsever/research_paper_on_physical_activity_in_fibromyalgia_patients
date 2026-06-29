#####
#Walk on: EMA study
#Analysis 
#last update: 07/03/2023
#####

######
#load libraries
##
library(esmpack)
library(remotes)
library(nlme)
library(lattice)
library(latticeExtra)
library(lme4)
library(dplyr)
library(lmerTest)
library(insight)

setwd("C:/Users/adpaepe/Documents/E-Health/PROJECT/BOF project/STUDIE 1/Analyses/Scripts")

source('Script data start + merge.R')

unique(data_all$token)

#exclude participants 
#wo002 - did not start the study (already excluded in previous script)
#wo006 - did not start the study (already excluded in previous script)
#wo005 - only data until December 12 (exclude here)
#wo006 - data begin study only half completed (already excluded in previous script)
#wo008 - only one notifications in SEMA3 (exclude here)
#wo016 - did not participate because of COVID-19 (exclude here)
#wo038 - no axivity data (exclude here)


#remark: participant 12 --> only 7 days of Axivity data!
#remark: participant 34 --> no data begin study

data_all <- data_all[which(data_all$token != "wo0382925" & data_all$token != "wo0058851" & 
                             data_all$token != "wo0087912" & data_all$token != "wo0162331"),]


length(unique(data_all$token)) #36 participants left
data_all$token <- droplevels(data_all$token)


data_all <- data_all[order(data_all$token, data_all$Day, data_all$Trigger_EMA),]



#frequency table for day and triggers
table(data_all$Day) #138 for day 1 (participant 13 and 23 only got 1 notification on day 1), 145 for day 4 (participant 1 received 5 notifications on day 4), 142 for day 13 (participant 4 only received 2 notifications on day 13) and 141 for day 14 (participant 4 only received 2 notifications on day 14 and participant 32 received only 1 notification)
table(data_all$Trigger_EMA) #501 for trigger 1, 501 for trigger 2, 501 for trigger 3, 501 for trigger 4 and 502 for trigger 4

length(data_all$Trigger_EMA) #2006 triggers in total

triggerperpp<-table(data_all$Day,data_all$Trigger_EMA, data_all$token)

#total number of triggers responded to
View(table(data_all$Day, is.na(data_all$COMPLETED_TS), data_all$token))

#exclude participants wo032 and wo019 because they responded to less than 1/3 (33% of the prompts)
data_all <- data_all[which(data_all$token!= "wo0327640" & data_all$token != "wo0193167"),]
unique(data_all$token)

#create variable beeptime and responstime (expressed in minutes after midnight)
data_all$CREATED_TS2 <- as.POSIXct(as.numeric(data_all$CREATED_TS), origin="1582/10/14", tz="GMT")
data$submitdate <- as.Date(as.POSIXct(data$submitdate))

data_all$trigger_TS_DateTime <- as.POSIXct(paste(data_all$trigger_TS_date,data_all$trigger_TS_time), format="%Y-%m-%d %H:%M:%S")
data_all$completed_TS_DateTime <- as.POSIXct(paste(data_all$completed_TS_date,data_all$completed_TS_time), format="%Y-%m-%d %H:%M:%S")

#time between notification and start questionnaire
data_all$RT <- difftime(data_all$trigger_ts, data_all$STARTED_TS)
mean(data_all$RT, na.rm=TRUE) #average response time of 77 seconds
median(data_all$RT, na.rm=TRUE) #median = 60 seconds
min(data_all$RT, na.rm=TRUE)
max(data_all$RT, na.rm=TRUE)


#time needed to complete questionnaire
data_all$CT <- difftime(data_all$COMPLETED_TS,data_all$STARTED_TS)
mean(data_all$CT, na.rm=TRUE) #average completion time of 77 seconds
median(data_all$CT, na.rm=TRUE) #60 seconds
range(data_all$CT, na.rm=TRUE)
max(data_all$CT, na.rm=TRUE)
sd(data_all$CT, na.rm=TRUE) #sd = 51 seconds

#time between adacent prompts

TimeTrigger1 <- data_all[which(data_all$Trigger_EMA ==1),]$SCHEDULED_TS
TimeTrigger2 <- data_all[which(data_all$Trigger_EMA ==2),]$SCHEDULED_TS
TimeTrigger3 <- data_all[which(data_all$Trigger_EMA ==3),]$SCHEDULED_TS
TimeTrigger4 <- data_all[which(data_all$Trigger_EMA ==4),]$SCHEDULED_TS

mean(difftime(TimeTrigger2,TimeTrigger1)) #2.5 hours
sd(difftime(TimeTrigger2,TimeTrigger1)) #0.23
mean(difftime(TimeTrigger3,TimeTrigger2)) #2.5 hours
sd(difftime(TimeTrigger3,TimeTrigger2)) #0.21
#mean(difftime(TimeTrigger4,TimeTrigger3)) #klopt iets niet


#change class variables
data_all$PIJN <- as.numeric(data_all$PIJN)
data_all$MOE <- as.numeric(data_all$MOE)
data_all$STRESS <- as.numeric(data_all$STRESS)
data_all$Day <- factor(data_all$Day)
data_all$EIGENEFF <- as.numeric(data_all$EIGENEFF)
data_all$INTENTIE <- as.numeric(data_all$INTENTIE)
data_all$UITKOMSTVERW <- as.numeric(data_all$UITKOMSTVERW)


#ability to move (yes/no)
prop.table(table(data_all$MOGELIJKHEID_BEW))
table(data_all$token, data_all$MOGELIJKHEID_BEW)

#select only data in which participants reported to be able to move
data_move <- data_all[which(data_all$MOGELIJKHEID_BEW == 1),]

#####
#Figures
##

#Explore temporal dynamics within individual - physical activity per day
ggplot(data_all,aes(x=Day,y=trigger_120_ENMO)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

#Explore temporal dynamics within individual - physical activity per trigger
ggplot(data_all,aes(x=Trigger_EMA,y=trigger_120_ENMO)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)
#somewhat more active in the morning

##Explore temporal dynamics within individual - pain per day
ggplot(data_all,aes(x=Day,y=PIJN)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

##Explore temporal dynamics within individual - pain per trigger
ggplot(data_all,aes(x=Trigger_EMA,y=PIJN)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

##Explore temporal dynamics within individual - fatigue per day
ggplot(data_all,aes(x=Day,y=MOE)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

##Explore temporal dynamics within individual - fatigue per trigger
ggplot(data_all,aes(x=Trigger_EMA,y=MOE)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

##Explore temporal dynamics within individual - stress per day
ggplot(data_all,aes(x=Day,y=STRESS)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)

##Explore temporal dynamics within individual - stress per trigger
ggplot(data_all,aes(x=Trigger_EMA,y=STRESS)) + geom_smooth(method = "lm",level = 0.95) + 
  geom_point() + facet_wrap(~token, nrow = 6, ncol = 6)


######
#Analyses
##
# add the person-level means to the dataset
data_all$mPIJN <- calc.mean(PIJN, token, data=data_all, expand=TRUE)
data_all$mMOE <- calc.mean(MOE, token, data=data_all, expand=TRUE)
data_all$mSTRESS <- calc.mean(STRESS, token, data=data_all, expand=TRUE)
data_all$mPA <- calc.mean(trigger_120_ENMO, token, data=data_all, expand=TRUE)

# create a new variable for the within-person mean centered variable
data_all$cPIJN <- calc.mcent(PIJN, token, data=data_all)
data_all$cMOE <- calc.mcent(MOE, token, data=data_all)
data_all$cSTRESS <- calc.mcent(STRESS, token, data=data_all)
data_all$cPA <- calc.mcent(trigger_120_ENMO, token, data=data_all)

# create a lagged version of variables
data_lagged <- data_all %>%
  group_by(token, Day) %>%
  dplyr::mutate(lcPIJN = lag(cPIJN, n=1, default=NA)) %>%
  dplyr::mutate(lmPIJN = lag(mPIJN, n=1, default=NA)) %>%
  dplyr::mutate(lcMOE = lag(cMOE, n=1, default=NA)) %>%
  dplyr::mutate(lmMOE = lag(mMOE, n=1, default=NA)) %>%
  dplyr::mutate(lcSTRESS = lag(cSTRESS, n=1, default=NA)) %>%
  dplyr::mutate(lmSTRESS = lag(mSTRESS, n=1, default=NA)) %>%
  dplyr::mutate(lcPA = lag(cPA, n=1, default=NA)) %>%
  dplyr::mutate(lmPA = lag(mPA, n=1, default=NA)) %>%
  dplyr::mutate(lPA = lag(trigger_120_ENMO, n=1, default=NA)) %>%
  dplyr::mutate(lPIJN = lag(PIJN, n=1, default=NA)) %>%
  dplyr::mutate(lMOE = lag(MOE, n=1, default=NA)) 
  
#Explore the distribution of the variables
hist(data_all$trigger_120_ENMO)
hist(data_move$trigger_120_ENMO)

hist(data_all$PIJN)
hist(data_all$MOE)
hist(data_all$STRESS)
hist(data_all$EIGENEFF)
hist(data_all$INTENTIE)
hist(data_all$UITKOMSTVERW)

######
#Explore variability within and between subjects and days
###
#PAIN
var_pain1 <- lmer(PIJN ~ 1 + (1|token), data=data_all)
summary(var_pain1)
rand(var_pain1) #significant effect

var <- get_variance(var_pain1) 
var$var.random/(var$var.residual+var$var.random) #59% of the variance can be explained by differences between subjects

#random subject intercept en random intercept voor dag: neem ook variantie binnen en tussen dagen in rekening
var_pain2 <- lmer(PIJN ~ 1 + (1|token/Day), data=data_all)
summary(var_pain2)

rand(var_pain2) #significant effect - significante variatie tussen subjecten en binnen een subject tussen dagen

var2 <- get_variance(var_pain2) 
var2$var.random/(var2$var.residual+var2$var.random) #72% of the variance is explained by differences between subjects and between days
var2$var.intercept[1]/(var2$var.residual+var2$var.random) #14% of the variance is explained by differences between days (within subject)
var2$var.intercept[2]/(var2$var.residual+var2$var.random) #58% of the variance is explained by differences between the subjects
var2$var.residual/(var2$var.residual+var2$var.random) #28% of the variance is explained by differences within subjects and within days 

#FATIGUE
var_fatigue1 <- lmer(MOE ~ 1 + (1|token), data=data_all)
summary(var_fatigue1)
rand(var_fatigue1) #significant effect

var <- get_variance(var_fatigue1) 
var$var.random/(var$var.residual+var$var.random) #58% of the variance can be explained by differences between subjects

#random subject intercept en random intercept voor dag: neem ook variantie binnen en tussen dagen in rekening
var_fatigue2 <- lmer(MOE ~ 1 + (1|token/Day), data=data_all)
summary(var_fatigue2)

rand(var_fatigue2) #significant effect - significante variatie tussen subjecten en binnen een subject tussen dagen

var2 <- get_variance(var_fatigue2) 
var2$var.random/(var2$var.residual+var2$var.random) #67% of the variance is explained by differences between subjects and between days
var2$var.intercept[1]/(var2$var.residual+var2$var.random) #9% of the variance is explained by differences between days (within subject)
var2$var.intercept[2]/(var2$var.residual+var2$var.random) #58% of the variance is explained by differences between the subjects
var2$var.residual/(var2$var.residual+var2$var.random) #33% of the variance is explained by differences within subjects and within days 


#STRESS
var_stress1 <- lmer(STRESS ~ 1 + (1|token), data=data_all)
summary(var_stress1)
rand(var_stress1) #significant effect

var <- get_variance(var_stress1) 
var$var.random/(var$var.residual+var$var.random) #59% of the variance can be explained by differences between subjects

#random subject intercept en random intercept voor dag: neem ook variantie binnen en tussen dagen in rekening
var_stress2 <- lmer(STRESS ~ 1 + (1|token/Day), data=data_all)
summary(var_stress2)

rand(var_stress2) #significant effect - significante variatie tussen subjecten en binnen een subject tussen dagen

var2 <- get_variance(var_stress2) 
var2$var.random/(var2$var.residual+var2$var.random) #69% of the variance is explained by differences between subjects and between days
var2$var.intercept[1]/(var2$var.residual+var2$var.random) #11% of the variance is explained by differences between days (within subject)
var2$var.intercept[2]/(var2$var.residual+var2$var.random) #59% of the variance is explained by differences between the subjects
var2$var.residual/(var2$var.residual+var2$var.random) #31% of the variance is explained by differences within subjects and within days 


#PA
var_PA1 <- lmer(trigger_120_ENMO ~ 1 + (1|token), data=data_all)
summary(var_PA1)
rand(var_PA1) #significant effect

var <- get_variance(var_PA1) 
var$var.random/(var$var.residual+var$var.random) #27% of the variance can be explained by differences between subjects

#random subject intercept en random intercept voor dag: neem ook variantie binnen en tussen dagen in rekening
var_PA2 <- lmer(trigger_120_ENMO ~ 1 + (1|token/Day), data=data_all)
summary(var_PA2)

rand(var_PA2) #randsignificant effect - randsignificante variatie tussen subjecten en binnen een subject tussen dagen

var2 <- get_variance(var_PA2) 
var2$var.random/(var2$var.residual+var2$var.random) #30% of the variance is explained by differences between subjects and between days
var2$var.intercept[1]/(var2$var.residual+var2$var.random) #3% of the variance is explained by differences between days (within subject)
var2$var.intercept[2]/(var2$var.residual+var2$var.random) #27% of the variance is explained by differences between the subjects
var2$var.residual/(var2$var.residual+var2$var.random) #70% of the variance is explained by differences within subjects and within days 


####
#2. Linear mixed effect models for the effect of pain (t1) on physical activity (t2)
#population level
fit1_pain <- lmer(trigger_120_ENMO ~ lcPIJN + lmPIJN + lPA + (1|token), data=data_lagged)
summary(fit1_pain)


####
#3. Linear mixed effect models for the effect of fatigue (t1) on physical activity (t2)
fit1_fatigue <- lmer(trigger_120_ENMO ~ lcMOE + lmMOE + lPA + (1|token), data=data_lagged)
summary(fit1_fatigue)

####
#4. Linear mixed effect models for the effect of physical activity (t1) on pain (t2)
fit1_pain2 <- lmer(PIJN ~ lcPA + lmPA + lPIJN + (1|token), data=data_lagged)
summary(fit1_pain2)

####
#5. Linear mixed effect models for the effect of physical activity (t1) on fatigue (t2)
fit1_fatigue2 <- lmer(trigger_120_ENMO ~ lcPA + lmPA + lMOE + (1|token), data=data_lagged)
summary(fit1_fatigue2)







