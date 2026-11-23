#stats_engine.py: should be used to make calculations for mean, median, mode, range, SD, t-test or ANOVA, linregress for line of best fit
#Shapiro-Wilk, and a normal-curve fit.

def describe(DATA): #returns mean, median, mode, range (min, max, and range of max-min), variance, SD, and n (number of samples)
    pass

def mode(DATA): 
    pass

def one_sample_ttest(DATA, mu): #needs pval, degrees of freedom (df), and t_stat
    pass

#the following values should have equal_var be default true if no value is provided, see how python does this.
def independent_ttest(DATA1, DATA2, equal_var):
    equal_var = True #for testing purposes, we will assume equal variance. This can be changed later if needed.
    pass

def paired_ttest(DATA1, DATA2): #needs pval, t_stat, df, and confidence interval
    pass

def one_way_anova(DATA1, DATA2, DATA3): #needs pval, f_stat, df_between, df_within
    pass

def linear_fit(DATA1, DATA2): #needs slope, intercept, r_value, p_value, std_err, r squared, and n from describe (use callbacks!)
    pass

def normality_test(DATA): #Shapiro-Wilk test, needs pval and W statistic
    pass

def histogram(DATA): #needs edges, counts, and density
    pass



