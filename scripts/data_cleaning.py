import pandas as pd

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
# Will remove these lines when done
df = df.drop(
    ['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
       '60_AvgPower', '50_AvgPower', 'ActiveIdle',
       '40_AvgPower','30_AvgPower','20_AvgPower','10_AvgPower',], axis=1)

###### Remember ^^^^^

# Clean make and model
df['HW_CPUName'].nunique() # how many distinct do we have?


df["CPU_Make"] = None
df.loc[df['HW_CPUName'].str.contains("Intel"), "CPU_Make"] = "Intel"
df.loc[df['HW_CPUName'].str.contains("AMD"), "CPU_Make"] = "AMD"

## How many do we have left?
df[df.CPU_Make.isna()] # Remember that for comparison you always get a truth matrix that you have to feed into the [] selecor
df.CPU_Make.isna().sum() ## Show only the count

## Which one is it exactly?
df[df.CPU_Make.isna()]['HW_CPUName']

## Move that to Intel
df.loc[df.CPU_Make.isna(), 'CPU_Make'] = "Intel"

## Now remove the Intel from the column HW.CPUName
df['HW_CPUName'] = df['HW_CPUName'].str.replace('Intel', "")
df['HW_CPUName'] = df['HW_CPUName'].str.replace('AMD', "")

# All the makes should now either be intel or AMD
assert (df['CPU_Make'].unique() == ("Intel", "AMD")).all()

df['HW_CPUName'].unique()

## look at all the brackets and try to spot pattern.
tb = df.HW_CPUName.str.match(".*\(\s*Turbo.*")

## how many? A: 41
df.loc[tb, 'HW_CPUName'].count()

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

#assert that HW_CPUName does not contain 'turbo'

## Now do the same, but with HW_CPUChars column
x = df.loc[df['HW_CPUChars'].str.match(".*\(.*Boost.*\)"), 'HW_CPUChars']
y = df.loc[df['HW_CPUChars'].str.match(".*\(.*up to (.*)GHz.*"), 'HW_CPUChars']
## What's different?
pd.concat([x,y]).drop_duplicates(keep=False)
#A: (Max Boost Clock up to 3.5 GHz)
df.iloc[445]
# I googled that CPU, its the same thing as Turbo Boost

df['TurboBoostGHz'] = df['HW_CPUChars'].str.extract(".*\(.*up to (.*)GHz.*")
df[df['TurboBoostGHz'].notna()] # How many do we have

# Strip TurboBoost from CPU Chars
df['HW_CPUChars'] = df['HW_CPUChars'].str.replace("\(.*up to (.*)GHz.*\)", "", regex=True)

## Make sure type is correct
df["TurboBoostGHz"] = df["TurboBoostGHz"].astype(float)
df.dtypes.to_dict()

# HW_CPUName
# @ X.X GHz -> this should be able to be safely removed, as the info already
# exists in the HW_CPUFreq column

df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*"), 'HW_CPUName']
df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*"), 'HW_CPUName'].count()
df.loc[df['HW_CPUName'].str.match(".*\d+\.\d*\s*GHz.*"), 'HW_CPUName'].unique()

## Compare the freq extract vs the freq in column, make sure they're ==
# Not really working ATM.
# Not sure how to compare these two Series together / Extract relevant info in comparable way
# I'm trying to get a extracted Series of substrings from CPUName ,
# And compare vs a value in the same row under HW_CPUFreq column
freq_from_name = df.HW_CPUName.str.extract(".*(\d+\.\d*)\s*GHz.*", expand = False)
freq_from_column = df.loc[df.HW_CPUName.str.match(".*\d+\.\d*\s*GHz.*"), 'HW_CPUFreq']
# assert (freq_from_name == (freq_from_column / 1000))


## HW_CPUName
# remember to strip @ sign
# and commas
#  Xeon Platinum 8176 CPU 2.10 GHz 
#   - strip 'CPU' 
# strip starting (R)
# strip starting and trailing \s
# strip \( and \)
#  Xeon Gold 6252 Processor
# normalize v#
#   [NAME]v#, [NAME] v#, [NAME]V#

## HW_CPUsEnabled
# Can be split into a few columns
# TotalCores
# Total chips
# data standardized, should be trivial
# leftover data: cores/chip
# - I think this can be skipped, its just the last two numbers divided


## CPU Characteristics
# Standardize X Core
# Quad,Octa,Hexa,Dual, -, w/o -, etc -> # Core
# Check # Core w/ core extracted from CPUs Enabled in prev. section
# Extract GHz, compare with FREQ, in same fashion as from CPUName
# Clean Core/Boost/Freq in similar fashion as before
# should be left with either L3 cache, L2 cache, Bus
# Mhz -> Bus
# X MB L3 Cache -> l3 cache, extract to column
# see what's left over and figure it out


## HW_HardwareThreads
# 8 (2 / core)
# first number relevant
# second number can be figured out from this / total cores, so shouldn't be needed
# write code to double check that first, similar to FREQ comparision code

## HW_PSUQuantAndRating
# can be split into 2 easily, always [1 x 900]
# NumOfPSU, PSURating

# HW_Vendor
# just basic cleaning, standardize how companies are written
# e.g. Hewlett Packard Enterprise -> Hewlett Packard
#      Hewlett-Packard Company    -> Hewlett Packard  
#      Hewlett-Packard            -> Hewlett Packard
# etc.

# HW_Model, HW_FormFactor
# Nothing for now