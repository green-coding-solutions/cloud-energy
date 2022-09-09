import pandas as pd
import re

"""
    This file reads the generated CSV file into a data frame
    and applies some cleaning and feature engineering to feed the data into 
    a linear model.
"""

pd.set_option("display.max_columns", 20)
pd.set_option('display.max_colwidth', None)

df = pd.read_csv(
    "./spec_data.csv", 
    sep="|", 
    index_col=False
)
df['hash'] = pd.util.hash_pandas_object(df)

## Cleaning 

# check if all the types are OK
df.dtypes.to_dict()

# Just for simplicity, remove columns that we currently do not need
df = df.drop(
    ['100_ActualLoad', '100_ssj_ops', "100_PerfPowerRatio",
       '90_ActualLoad', '90_ssj_ops',  '90_PerfPowerRatio',
       '80_ActualLoad', '80_ssj_ops',  '80_PerfPowerRatio',
       '70_ActualLoad', '70_ssj_ops',  '70_PerfPowerRatio',
       '60_ActualLoad', '60_ssj_ops',  '60_PerfPowerRatio',
       '50_ActualLoad', '50_ssj_ops',  '50_PerfPowerRatio',
       '40_ActualLoad', '40_ssj_ops',  '40_PerfPowerRatio',
       '30_ActualLoad', '30_ssj_ops',  '30_PerfPowerRatio',
       '20_ActualLoad', '20_ssj_ops',  '20_PerfPowerRatio',
       '10_ActualLoad', '10_ssj_ops',  '10_PerfPowerRatio'], axis=1)


# TEMP: Drop unneeded columns just to make reading DF easier
# TODO: Will remove these lines when done
df = df.drop(
    ['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
       '60_AvgPower', '50_AvgPower', 'ActiveIdle',
       '40_AvgPower','30_AvgPower','20_AvgPower','10_AvgPower',], axis=1)

###### Remember ^^^^^

# Clean make and model
df['HW_CPUName'].nunique() # how many distinct do we have?


df["CPUMake"] = None
df.loc[df['HW_CPUName'].str.contains("Intel"), "CPUMake"] = "Intel"
df.loc[df['HW_CPUName'].str.contains("AMD"), "CPUMake"] = "AMD"

## How many do we have left?
df[df.CPUMake.isna()] # Remember that for comparison you always get a truth matrix that you have to feed into the [] selecor
df.CPUMake.isna().sum() ## Show only the count

## Which one is it exactly?
df[df.CPUMake.isna()]['HW_CPUName']

## Move that to Intel
df.loc[df.CPUMake.isna(), 'CPUMake'] = "Intel"

## Now remove the Intel from the column HW.CPUName
df['HW_CPUName'] = df['HW_CPUName'].str.replace('Intel', "")
df['HW_CPUName'] = df['HW_CPUName'].str.replace('AMD', "")

# All the makes should now either be intel or AMD
assert (df['CPUMake'].unique() == ("Intel", "AMD")).all()

df['HW_CPUName'].unique()

## look at all the brackets and try to spot pattern.
df.HW_CPUName.str.match(".*\(\s*Turbo.*")

## how many? A: 41
df.loc[df.HW_CPUName.str.match(".*\(\s*Turbo.*"), 'HW_CPUName'].count()

# Create TurboBoost column
df["TurboBoostGHz"] = None

# Check HW_CPUName column / count
df.loc[df['HW_CPUName'].str.match(".*\(.*Turbo.*\)"), 'HW_CPUName'].count()
df.loc[df['HW_CPUName'].str.match(".*\(.*up to (.*)GHz.*"), 'HW_CPUName'].count()

# Fill column from CPU Name data
df['TurboBoostGHz'] = df['HW_CPUName'].str.extract(".*\(.*up to (\d+\.\d+)\s*GHz.*")
df[df['TurboBoostGHz'].notna()] # How many do we have
## looks correct

# Remove Turbo Boost
df['HW_CPUName'] = df['HW_CPUName'].str.replace("\(.*Turbo.*\)", "", regex=True)

#TODO: assert that HW_CPUName does not contain 'turbo'

## Now do the same, but with HW_CPUChars column
x = df.loc[df['HW_CPUChars'].str.match(".*\(.*Boost.*\)"), 'HW_CPUChars']
y = df.loc[df['HW_CPUChars'].str.match(".*\(.*up to (.*)GHz.*"), 'HW_CPUChars']
## What's different?
pd.concat([x,y]).drop_duplicates(keep=False)
#A: (Max Boost Clock up to 3.5 GHz)
#df.iloc[445]
# I googled that CPU, its the same thing as Turbo Boost


### Merge (actually fillna()) the two TurboBoostGHz columns
turbo_from_chars = df['HW_CPUChars'].str.extract(r'.*\(.*up to (?P<TurboBoostGHz>.*)GHz.*')
turbo_from_chars.count()      # 91
df['TurboBoostGHz'].count()   # 41
df['TurboBoostGHz'] = df['TurboBoostGHz'].fillna(turbo_from_chars['TurboBoostGHz'])
df['TurboBoostGHz'].count()  # 132, looks good considering duplicates

# Strip TurboBoost from CPU Chars
df['HW_CPUChars'] = df['HW_CPUChars'].str.replace("\(.*up to (.*)GHz.*\)", "", regex=True)

## Make sure type is correct
df["TurboBoostGHz"] = df["TurboBoostGHz"].astype(float)
df.dtypes.to_dict()

# HW_CPUName
# @ X.X GHz -> this should be able to be safely removed, as the info already
# exists in the HW_CPUFreq column

df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName']
df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName'].count()
df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*", case=False), 'HW_CPUName'].unique()


## Compare the freq extract vs the freq in column, make sure they're ==
freq_from_name = df.HW_CPUName.str.extract(".*(\d+\.\d*)\s*GHz.*", expand = False, flags=re.IGNORECASE).dropna()
freq_from_column = df.loc[freq_from_name.index]
freq_from_name = freq_from_name.astype('float') * 1000
freq_from_column.HW_CPUFreq = freq_from_column.HW_CPUFreq.astype('float')
### What's a simple way to see everywhere this fails?
#x = freq_from_column.loc[~freq_from_name.eq(freq_from_column.HW_CPUFreq)]
#df.loc[x.index, x.hash] == df.hash
#assert(freq_from_name.eq(freq_from_column.HW_CPUFreq).all()

#z = freq_from_name.eq(freq_from_column) ### Line 484 is false
# 484 in freq_from_name is 2933
# 484 in freq_from_column is 2930
# oh its a rounding error. hmm. what do here. could just drop. not best long
# thinking though.
# TODO: for now this is fine, it means we can safely remove these values, 
# but I want to turn this assert back on
# clean line 484 manually, then use the assert :-)
# hash the row


### HW_CPUName
# Remove Frequency data#  Xeon Gold 6252 Processor
df['HW_CPUName'] = df['HW_CPUName'].str.replace("\d+\.\d*\s*GHz", "", regex=True,case=False)

## Strip away some things
# Starting (R)
df['HW_CPUName'] = df['HW_CPUName'].str.replace("^\(R\)", "", regex=True,case=False)
# remove chars: @(), 
df['HW_CPUName'] = df['HW_CPUName'].str.replace("[@\(\),]", "", regex=True)
# Remove 'CPU' and 'Processor' that kinda randomly appears
df['HW_CPUName'] = df['HW_CPUName'].str.replace("CPU", "", regex=True) # should this be case insensitive?
df['HW_CPUName'] = df['HW_CPUName'].str.replace("Processor", "", regex=True, case=False)

# normalize v#
#   [NAME]v#, [NAME] v#, [NAME]V#
# Standarize into [NAME] v#, as that is how they show up on intel ark's search
df['HW_CPUName'] = df['HW_CPUName'].str.replace("\s*v\s?(\d)", " v\\1", regex=True, case=False)

# trim whitespace at start and end
df['HW_CPUName'] = df['HW_CPUName'].str.replace("^\s|\s$", "", regex=True)
# Condense leftover whitespaces
df['HW_CPUName'] = df['HW_CPUName'].str.replace("\s\s+", " ", regex=True)

## TODO: Check for 4 letter digits, how many duplicates they are within the uniques?
cpu_unique = df['HW_CPUName'].unique()

## HW_CPUsEnabled
# X cores, X chips, X cores/chip
# split into CPUCores, CPUChips. Cast as Int. Ignore cores/chips
df['CPUCores'] = df.HW_CPUsEnabled.str.extract("^\s*(\d+)\s*cores?\s*,.*", flags=re.IGNORECASE).astype(int)
df['CPUChips'] = df.HW_CPUsEnabled.str.extract(".*,\s*(\d)+\s*chips?,.*", flags=re.IGNORECASE).astype(int)
assert df[df.CPUCores.isna()].empty
assert df[df.CPUChips.isna()].empty
df.drop('HW_CPUsEnabled', axis=1)

## HW_HardwareThreads
# 8 (2 / core)
# first number relevant
# second number can be figured out from this / total cores, so shouldn't be needed
# write code to double check that first, similar to FREQ comparision code
df['CPUThreads'] = df.HW_HardwareThreads.str.extract("^\s*(\d+)\s*\(.*").astype(int)
thread_per_core = df['CPUThreads']  / df['CPUCores'] 
thread_per_core_extract = df.HW_HardwareThreads.str.extract(".*\((\d+)\s*/", expand=False).dropna().astype(int)
assert (thread_per_core.eq(thread_per_core_extract).all())
df.drop('HW_HardwareThreads', axis=1)


## HW_PSUQuantAndRating
# can be split into 2 easily
#   2 x 700W
#   1 x 1100
# NumOfPSU, PSURating
# don't drop yet
df['NumOfPSU'] = df.HW_PSUQuantAndRating.str.extract("^\s*(\d+)\s*x.*").astype('float')
df['PSURating'] = df.HW_PSUQuantAndRating.str.extract(".*x\s*(\d+).*").astype('float')
# urgh there's at least one 'None' in there
# that's a problem when we try to cast .astype(int)
# but apparently not when we use 'float' :-/ C'mon, pandas
df.dtypes.to_dict()

## Assert that all is good here
# well since some of them are actually empty, not sure what to actually check for
# TODO: think
#assert df[df.NumOfPSU.isna()].empty
#assert df[df.PSURating.isna()].empty

# TODO: HW_Vendor
# just basic cleaning, standardize how companies are written
# etc.
vendors = df.loc[df['HW_Vendor'].str.contains('Hewlett'), 'HW_Vendor'].unique()
#df.HW_Vendor = df.HW_Vendor.str.replace('HEPYCEPYCewlett\s?-?\s?Packard\s?(Enterprise|Company)', '', regex=True, case=False)


## Column with cpu family
# do by known names - Xeon, Opteron, etc.
## Xeon , Opteron , EPYC , 
# do unique, figure it out from there
df['CPUFamily'] = None
pat = "(xeon)|(opteron)|(epyc)|(i3)|(i5)"
cpu_fam_1 = df.loc[df['HW_CPUName'].str.contains("(xeon)|(opteron)|(epyc)", case=False)]
cpu_fam_2 = df.loc[df['HW_CPUName'].str.contains("(i3)|(i5)", case=False)]
leftover = df.loc[~df['HW_CPUName'].str.contains(pat, case=False)]
# E3-1260L v5 , Pentium D 930 , X3350
#    Xeon^    ,    Penti      ,  Xeon^ 
df.loc[df['HW_CPUName'].str.contains('X3350', case=False)]
z = df.loc[df['HW_CPUName'].str.contains('E3-1260L v5', case=False)]

## CPUFamily fill
df.loc[df['HW_CPUName'].str.contains("xeon", case=False), "CPUFamily"] = "Xeon"
df.loc[df['HW_CPUName'].str.contains("opteron", case=False), "CPUFamily"] = "Opteron"
df.loc[df['HW_CPUName'].str.contains("epyc", case=False), "CPUFamily"] = "EPYC"
df.loc[df['HW_CPUName'].str.contains("i3", case=False), "CPUFamily"] = "i3"
df.loc[df['HW_CPUName'].str.contains("i5", case=False), "CPUFamily"] = "i5"
df.loc[df['HW_CPUName'].str.contains("Pentium", case=False), "CPUFamily"] = "Pentium"
## Leftover Xeon's
df.loc[df['HW_CPUName'].str.contains("(X3350)|(E3-1260L)", case=False), "CPUFamily"] = "Xeon"

## Assert CPU Family
assert(df.CPUFamily.isna().sum() == 0)

## L3 Cache, as #
df['L3CacheKB'] = None
mb_pat_l3='^\s*(?P<L3Cache>\d+)\s*mb' # remember case=False
kb_pat_l3='^\s*(?P<L3Cache>\d+)\s*kb' # remember case=False
mb_l3 = df.HW_TertiaryCache.str.extract(mb_pat_l3, flags=re.IGNORECASE).astype('float') * 1000
kb_l3 = df.HW_TertiaryCache.str.extract(kb_pat_l3, flags=re.IGNORECASE).astype('float')
df['L3CacheKB'] = mb_l3
df['L3CacheKB'] = df['L3CacheKB'].fillna(kb_l3['L3Cache'])
assert(~df.loc[df['L3CacheKB'].isna(), 'HW_TertiaryCache'].isna()).all()
## TODO: Is line 610 a mistake?? Original data says  39424 MB.... the line above has 39242 KB....

## L2 Cache
df['L2CacheKB'] = None
mb_pat_l2='^\s*(?P<L2Cache>\d+)\s*mb' # remember flags=re.IGNORECASE)
kb_pat_l2='^\s*(?P<L2Cache>\d+)\s*kb' # remember flags=re.IGNORECASE)
mb_l2 = df.HW_SecondaryCache.str.extract(mb_pat_l2, flags=re.IGNORECASE).astype('float') * 1000
kb_l2 = df.HW_SecondaryCache.str.extract(kb_pat_l2, flags=re.IGNORECASE).astype('float')
df['L2CacheKB'] = mb_l2
df['L2CacheKB'] = df['L2CacheKB'].fillna(kb_l2['L2Cache'])
assert(~df.loc[df['L2CacheKB'].isna(), 'HW_SecondaryCache'].isna()).all()
## TODO: Line 103 also seems stupidly big


## TODO: Column with microarchitecture
import glob
import re

## Import David Mytton's arch data into a dataframe
files = glob.glob("./../data/cpu_arch/*.csv")
li = []
for f in files:
    pat='([^/]*).csv$'
    header = re.search(pat,f).group(1)
    csv = pd.read_csv(f, sep="|",header=None, names=[header])
    li.append(csv)
archs = pd.concat(li, axis=0, ignore_index=True)

df['arch'] = None

# urgh i think i have to clean the family name, at least for xeon
#clean xeon
df['HW_CPUName'] = df['HW_CPUName'].str.replace("Xeon", "", regex=True)


intel_haswell = df.HW_CPUName.isin(archs['intel-haswell'])
intel_ivybridge = df.HW_CPUName.isin(archs['intel-ivybridge'])
intel_skylake = df.HW_CPUName.isin(archs['intel-skylake'])
amd_epyc_gen3 = df.HW_CPUName.isin(archs['amd-epyc-gen3'])
amd_epyc_gen2 = df.HW_CPUName.isin(archs['amd-epyc-gen2'])
amd_epyc_gen1 = df.HW_CPUName.isin(archs['amd-epyc-gen1'])
intel_sandybridge = df.HW_CPUName.isin(archs['intel-sandybridge'])
intel_broadwell = df.HW_CPUName.isin(archs['intel-broadwell'])
intel_cascadelake = df.HW_CPUName.isin(archs['intel-cascadelake'])
intel_coffeelake = df.HW_CPUName.isin(archs['intel-coffeelake'])

# test code
# a_archs_t = pd.DataFrame({'XeonPeon':['CoolProcessorWon 1234', 'CoolProcessorToo 4321', None, None],'OptimusPrime':[None, None, 'CoolProcessorTree', 'CoolProcessorFore'],})
# a_df_t = pd.DataFrame({'CPU': ['CoolProcessorWon 1234', 'Totally Not In DataSet','CoolProcessorWon', 'CoolProcessorFore', 'CoolProcessor']})
# a_t = a_df_t.CPU.isin(a_archs_t.XeonPeon)

## Disk Drive, size + type (SSD or HDD)


















