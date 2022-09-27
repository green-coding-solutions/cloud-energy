import re
import glob
import pandas as pd
import include.helper_functions as helper

"""
    This file reads the generated CSV file into a data frame
    and applies some cleaning and feature engineering to feed the data into
    a linear model.

    If the SPECPower data ever gets updated please walk this file manually
    from top to bottom.

    In the file some asserts are given, but also manual checks should be run
"""


def remove_unneeded_columns(df_original):
    df = df_original.copy()
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
    helper.columns_diff(df, df_original)
    return df

def split_hardware_availabilty(df_original):
    df = df_original.copy()

    availability = df["Hardware Availability"].str.split("-", expand=True)
    df["Hardware_Availability_Month"] = availability[0]
    df["Hardware_Availability_Year"]  = availability[1]
    df["Hardware_Availability_Year"] =  df["Hardware_Availability_Year"].astype(int)

    return df

def melt_power_and_load(df_original):
    df = df_original.copy()

    melt_columns = ['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
           '60_AvgPower', '50_AvgPower', '40_AvgPower', '30_AvgPower',
           '20_AvgPower', '10_AvgPower', 'ActiveIdle']
    remaining_columns = df.columns[~df.columns.isin(melt_columns)]

    df = df.melt(
        id_vars=remaining_columns,
        value_vars=melt_columns,
        var_name='utilization',
        value_name="power",
    )

    helper.columns_diff(df, df_original)
    return df

def clean_power_and_load(df_original):
    df = df_original.copy()
    df.utilization = df.utilization.str.replace('ActiveIdle', '0')
    df.utilization = df.utilization.str.replace('100_AvgPower', '100')
    df.utilization = df.utilization.str.replace('90_AvgPower', '90')
    df.utilization = df.utilization.str.replace('90_AvgPower', '90')
    df.utilization = df.utilization.str.replace('80_AvgPower', '80')
    df.utilization = df.utilization.str.replace('70_AvgPower', '70')
    df.utilization = df.utilization.str.replace('60_AvgPower', '60')
    df.utilization = df.utilization.str.replace('50_AvgPower', '50')
    df.utilization = df.utilization.str.replace('40_AvgPower', '40')
    df.utilization = df.utilization.str.replace('30_AvgPower', '30')
    df.utilization = df.utilization.str.replace('20_AvgPower', '20')
    df.utilization = df.utilization.str.replace('10_AvgPower', '10')

    df.utilization = df.utilization.astype(int)
    helper.same_column_diff(df, df, 'utilization')


    return df


def create_cpu_make(df_original):
    df = df_original.copy()
    df["CPUMake"] = None

    assert df.loc[(df['HW_CPUName'].str.contains("Intel", case=False)) & (df['HW_CPUName'].str.contains("AMD", case=False)), "CPUMake"].empty # Intel and AMD never in one column

    df.loc[df['HW_CPUName'].str.contains("Intel"), "CPUMake"] = "intel"
    df.loc[df['HW_CPUName'].str.contains("AMD"), "CPUMake"] = "amd"


    ## How many do we have left?
    df[df.CPUMake.isna()].HW_CPUName

    ## Currently we only see the Xeon L5420 @Dan: Was not specific
    df.loc[df.HW_CPUName== "Xeon L5420", "CPUMake"] = "intel"

    helper.new_column_diff(df, 'HW_CPUName', 'CPUMake')


    # All the makes should now either be intel or AMD
    assert list(df['CPUMake'].unique()) == ["intel", "amd"], "CPUMake contained vendors other than AMD / Intel"

    return df

def create_cpu_name(df_original):
    df = df_original.copy()

    df['CPUName'] = df['HW_CPUName']


    ## Now remove the vendor from the column and generate a new
    df['CPUName'] = df['CPUName'].str.replace(r'Intel\s*', "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r'AMD\s*', "", regex=True, flags=re.IGNORECASE)


    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Intel\s*Turbo\s*Boost\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Turbo\s*Boost\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*Turbo\s*CORE\s*Technology\s*up\s*to\s*\d+\.\d*\s*GHz\s*\)", "", regex=True, flags=re.IGNORECASE)
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*\d+\.\d*\s*GHz\s*\)", "", regex=True,flags=re.IGNORECASE) # remove only frequency
    df['CPUName'] = df['CPUName'].str.replace(r"\(\s*r\s*\)", "", regex=True,flags=re.IGNORECASE) # remove (r)
    df['CPUName'] = df['CPUName'].str.replace(r"Processor\s*", "", regex=True,flags=re.IGNORECASE) # remove Processor
    df['CPUName'] = df['CPUName'].str.replace(r"@?\s*\d+\.\d*\s*GHz\s*", "", regex=True,flags=re.IGNORECASE) # remove @ 2.3 GHz
    df['CPUName'] = df['CPUName'].str.replace(r"CPU\s*", "", regex=True,flags=re.IGNORECASE) # remove CPU
    df['CPUName'] = df['CPUName'].str.replace(r"\w+-Core\s*", "", regex=True,flags=re.IGNORECASE) # remove Quad-Core etc.
    df['CPUName'] = df['CPUName'].str.replace(r",\s*", "", regex=True,flags=re.IGNORECASE) # remove ,

    # Unique cases
    df['CPUName'] = df['CPUName'].str.replace("Dell SKU [338-BNCG]", "", regex=False) # remove special case Dell SKU [338-BNCG]
    df.loc[df.CPUName == 'X3350', 'CPUName'] = 'xeonx3350'
    df.loc[df.CPUName == 'E3-1260L v5', 'CPUName'] = 'xeone3-1260lv5'
    df.loc[df.CPUName == 'Xeon', 'CPUName'] = 'xeon-undefined' # move to XeonUNDEFINED so the model will later have no false-positive match for "Xeon"

    df['CPUName'] = df['CPUName'].str.replace(r"\s*", "", regex=True) # normalize
    df.CPUName = df.CPUName.str.lower() # normalize

    assert df[~df.CPUName.str.match(r"opteron|xeon|epyc|pentium|corei3|corei5|corei7")].CPUName.empty, "Unknown processors in CPUName apart from Opteron|Xeon|EPYC|Pentium|Corei3|Corei5|Corei7"

    assert df[df['CPUName'].str.contains('(', regex=False)].empty, "Still brackets () in CPUName"

    # validate what we have as uniques
    helper.visual_check(df.CPUName.unique(), "All names ok?") #DEBUG

    helper.new_column_diff(df, 'HW_CPUName', 'CPUName')

    return df

def create_turbo_boost(df_original):
    df = df_original.copy()

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

    helper.new_column_diff(df, 'HW_CPUName', 'TurboBoostGHz')

    return df

# X cores, X chips, X cores/chip
def make_cpu_cores(df_original):
    df = df_original.copy()
    df['CPUCores'] = df.HW_CPUsEnabled.str.extract("^\s*(\d+)\s*cores?\s*,.*", flags=re.IGNORECASE).astype(int)
    assert df[df.CPUCores.isna()].empty , "CPUCores contains NA"
    helper.new_column_diff(df, 'CPUCores', 'HW_CPUsEnabled')
    # recover original column
    df.HW_CPUsEnabled = df_original.HW_CPUsEnabled
    return df

def make_cpu_chips(df_original):
    df = df_original.copy()
    df['CPUChips'] = df.HW_CPUsEnabled.str.extract(".*,\s*(\d)+\s*chips?,.*", flags=re.IGNORECASE).astype(int)
    assert df[df.CPUChips.isna()].empty, "CPUChips contains NA"
    helper.new_column_diff(df, 'CPUChips', 'HW_CPUsEnabled')
    df.HW_CPUsEnabled = df_original.HW_CPUsEnabled
    return df


# 8 (2 / core)
# first number relevant
# second number can be figured out from this / total cores, so shouldn't be needed
# write code to double check that first, similar to FREQ comparision code

def make_hardware_threads(df_original):
    df = df_original.copy()
    df.HW_HardwareThreads.unique() # DEBUG
    df['CPUThreads'] = df.HW_HardwareThreads.str.extract("^\s*(\d+)\s*\(.*").astype(int)
    thread_per_core = df['CPUThreads']  / df['CPUCores']
    thread_per_core_extract = df.HW_HardwareThreads.str.extract("\((\d+)\s*\/\s*core\)", expand=False, flags=re.IGNORECASE).dropna().astype(int)
    assert thread_per_core.eq(thread_per_core_extract).all(), "Threads per core was not equal to comparison via calculation"

    return df

# can be split into 2 easily
#   2 x 700W
#   1 x 1100
# NumOfPSU, PSURating
def split_psu(df_original):
    df = df_original.copy()

    df.HW_PSUQuantAndRating.unique()

    df['NumOfPSU'] = df.HW_PSUQuantAndRating.str.extract("^\s*(\d+)\s*x.*")
    df['NumOfPSU'] = df['NumOfPSU'].astype('Int64')
    df['PSURating'] = df.HW_PSUQuantAndRating.str.extract(".*x\s*(\d+).*").astype('Int64')
    df['PSURating'] = df['PSURating'].astype('Int64')

    ## Assert that all is good here
    # well since some of them are actually empty, not sure what to actually check for

    # 6 (66 expanded) rows are empty is allowed with the specified hashes ...
    # but somehow the hash column is gone and I cannot reference it ... why?
    #assert df.drop(df.hash)[df.NumOfPSU.isna()].empty
    #assert df[df.PSURating.isna()].empty

    assert df.NumOfPSU.isna().sum() == 6, "PSU was not 6"
    return df


## Column with cpu family
# do by known names - Xeon, Opteron, etc.
## Xeon , Opteron , EPYC ,
# do unique, figure it out from there
def make_cpu_family(df_original):
    df = df_original.copy()
    df['CPUFamily'] = None
    pat = r"xeon|opteron|epyc|i3|i5|pentium"

    assert df.loc[~df['CPUName'].str.contains(pat, regex=True)].CPUName.empty, "Unknown family found"


    possible_families = [
        df.loc[df['CPUName'].str.contains("xeon"), "CPUName"],
        df.loc[df['CPUName'].str.contains("opteron"), "CPUName"],
        df.loc[df['CPUName'].str.contains("epyc"), "CPUName"],
        df.loc[df['CPUName'].str.contains("i3"), "CPUName"],
        df.loc[df['CPUName'].str.contains("i5"), "CPUName"],
        df.loc[df['CPUName'].str.contains("pentium"), "CPUName"]
    ]

    for i, possible_family in enumerate(possible_families):
        for j in range(i+1, len(possible_families)):
            # print(f"Checking {possible_family.iloc[0]} and {possible_families[j].iloc[0]}")
            assert possible_family.index.intersection(possible_families[j].index).empty, f"Possible families had overlap - between {possible_family.iloc[0]} and {possible_families[j].iloc[0]}"


    ## CPUFamily fill
    df.loc[df['CPUName'].str.contains("xeon"), "CPUFamily"] = "xeon"
    df.loc[df['CPUName'].str.contains("opteron"), "CPUFamily"] = "opteron"
    df.loc[df['CPUName'].str.contains("epyc"), "CPUFamily"] = "epyc"
    df.loc[df['CPUName'].str.contains("i3"), "CPUFamily"] = "core-i3"
    df.loc[df['CPUName'].str.contains("i5"), "CPUFamily"] = "core-i5"
    df.loc[df['CPUName'].str.contains("pentium"), "CPUFamily"] = "pentium"

    ## Assert CPU Family

    assert df.CPUFamily.isna().sum() == 0, "CPUFamily contained NA"
    return df


def make_l2_cache(df_original):
    df = df_original.copy()
    ## L2 Cache
    df['L2CacheKB'] = None
    mb_pat_l2='^\s*(?P<L2Cache>\d+)\s*mb' # remember flags=re.IGNORECASE)
    kb_pat_l2='^\s*(?P<L2Cache>\d+)\s*kb' # remember flags=re.IGNORECASE)
    mb_l2 = df.HW_SecondaryCache.str.extract(mb_pat_l2, flags=re.IGNORECASE).astype('float') * 1000
    kb_l2 = df.HW_SecondaryCache.str.extract(kb_pat_l2, flags=re.IGNORECASE).astype('float')
    df['L2CacheKB'] = mb_l2
    df['L2CacheKB'] = df['L2CacheKB'].fillna(kb_l2['L2Cache'])
    assert df['L2CacheKB'].isna().any() == False, "L2Cache contained empties"
    ## TODO: Line 103 also seems stupidly big

    return df

def make_l3_cache(df_original):
    df = df_original.copy()
    ## L3 Cache, as #
    df['L3CacheKB'] = None
    mb_pat_l3='^\s*(?P<L3Cache>\d+)\s*mb' # remember case=False
    kb_pat_l3='^\s*(?P<L3Cache>\d+)\s*kb' # remember case=False
    mb_l3 = df.HW_TertiaryCache.str.extract(mb_pat_l3, flags=re.IGNORECASE).astype('float') * 1000
    kb_l3 = df.HW_TertiaryCache.str.extract(kb_pat_l3, flags=re.IGNORECASE).astype('float')
    df['L3CacheKB'] = mb_l3
    df['L3CacheKB'] = df['L3CacheKB'].fillna(kb_l3['L3Cache'])

    # There is a typo in the L3 cache size. It is kb not MB, but only for these allowed processors
    list(df[df['L3CacheKB'] > 39423000.0].CPUName.unique()) == ['XeonPlatinum8176', 'XeonPlatinum8280', 'XeonPlatinum8276L']

    df.loc[df['L3CacheKB'] > 39422000.0, 'L3CacheKB']
    df.loc[df['L3CacheKB'] > 39423000.0, 'L3CacheKB'] = 39424.0
    assert df['L3CacheKB'].isna().sum() == 85, f"L3Cache contained more than 85 empties: {df['L3CacheKB'].isna().sum()}"

    return df


# This function is not used anymore
# Problem being that only 50% of the architecture was matched! Rest was still NA
def make_architecture_old(df_original):
    df = df_original.copy()

    ## Import David Mytton's arch data into a dataframe
    files = glob.glob("./../data/cpu_arch/*.csv")
    pat='(intel|amd)-([^/]*).csv$'
    arch = pd.DataFrame(columns=['architecture', 'value'])
    for f in files:
        header = re.search(pat,f).group(2)
        f
        csv = pd.read_csv(f, sep="|",header=None, names=[header])
        csv = csv.melt(id_vars=None, value_vars=[header], var_name="architecture")
        arch = arch.append(csv, ignore_index=True)

    arch

    df['Architecture'] = None
    clean_names = df.CPUName.str.replace(r"xeon|opteron|core", "", regex=True)

    assert arch.value.nunique() == arch.shape[0], "Duplicate entries where in architecture lookup file"


    arch.value = arch.value.str.lower().str.replace(r"\s*", "", regex=True) # normalize

    for i, clean_name in clean_names.iteritems():
        found_architecture = arch[arch.value == clean_name].architecture
        assert len(found_architecture) < 2
        if not found_architecture.empty:
            df.loc[i,'Architecture'] = found_architecture.iloc[0]


    # opteron is known
    df.loc[df['CPUName'].str.contains('opteron'), 'Architecture'] = 'opteron'


    assert df[df['Architecture'].isna()].CPUName.unique().shape[0] == 59, "More than 59 unique unknown architectures found!"

    return df

# This function was based on the Intel HTML files. But it has still over 50% missing ...
def make_tdp_old(df_original):
    df = df_original.copy()

    ## Import David Mytton's arch data into a dataframe
    amd = pd.read_csv("../data/cpu_spec_sheets/amd.csv")

    df["TDP"] = None

    clean_amd_names = df[df.CPUMake == "amd"].CPUName.str.replace(r"xeon|opteron|core", "", regex=True) # normalize
    amd['models_clean'] = amd.Model.str.replace("™", "").str.replace("AMD ", "").str.replace(r"\s*","", regex=True).str.lower() # normalize

    # amd['models_clean'].value_counts() # array is NOT unique. but the non-unique are currently no problem
    # we assert for that in the loop

    for i, clean_amd_name in clean_amd_names.iteritems(): # be vary not to use enumerate() as you will not get the real index, but a re-keyed list
        matching_processors = amd[amd.models_clean == clean_amd_name]
        assert matching_processors.shape[0] < 2, f"Found more than one processor to match with TDP for {clean_amd_name}"
        if not matching_processors.empty:
            df.loc[i, "TDP"] = matching_processors["Default TDP"].str.replace('W', "").iloc[0]


    df.loc[df.TDP == "155/170", "TDP"] = 170 # Correct for AMD unclear spec to upper bound


    intel_files = glob.glob("./../data/cpu_spec_sheets/*.html")
    intel_tdps = pd.DataFrame(columns=['Processor Number', 'TDP'])


    for f in intel_files:
        tables = pd.read_html(f)
        assert len(tables) == 1, f"More than one table ({len(tables)}) in Intel ARK download file: {f}"

        table = tables[0]
        tdp_columns = table[table.iloc[:,0] == 'TDP'].index.values
        processor_number_columns = table[table.iloc[:,0] == 'Processor Number'].index.values
        assert len(tdp_columns) == 1, f"More than one column ({len(tdp_columns)}) for TDP in Intel ARK download file: {f}"
        assert len(processor_number_columns) == 1, f"More than one column ({len(processor_number_columns)}) for Processor Number in Intel ARK download file: {f}"

        # now it is ok to transpose
        tp = table.transpose()
        tp.columns = tp.iloc[0]
        tp = tp.drop(tp.index[0], axis=0)


        # manually looked up on Intel.Ark.com
        tp.loc[tp['Processor Number'] == 'W-11855M', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11865MRE', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11555MRE', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11155MRE', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11955M', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11855M', 'TDP'] = 45
        tp.loc[tp['Processor Number'] == 'W-11865MRE', 'TDP'] = 45


        assert tp.TDP.isna().sum() == 0, f"TDP was not null for following models: {tp.loc[tp.TDP.isna(),'Processor Number']}"


        assert (tp.loc[:, ["Processor Number", "TDP"]].groupby("Processor Number").nunique() == 1).all().all(), "Found conflicting info for processor type and TDP"

        print(tp.loc[:, ['Processor Number', 'TDP']].shape)
        intel_tdps = intel_tdps.append(tp.loc[:, ['Processor Number', 'TDP']], ignore_index=True)

    intel_tdps['Processor Number'] = intel_tdps['Processor Number'].str.replace(r"\s*", "", regex=True).str.lower()
    intel_tdps['TDP'] = intel_tdps['TDP'].str.replace("W", "").str.replace(r"\s*", "", regex=True)


    intel_tdps['Processor Number'].value_counts() # NOT unique. But we have no TDP Overlap. So we make it unique
    intel_tdps = intel_tdps.drop_duplicates(subset=["Processor Number"])


    clean_intel_names = df[df.CPUMake == "intel"].CPUName.str.replace(r"xeon|opteron|core", "", regex=True) # normalize

    for i, clean_intel_name in clean_intel_names.iteritems(): # be vary not to use enumerate() as you will not get the real index, but a re-keyed list
        matching_processors = intel_tdps[intel_tdps['Processor Number'] == clean_intel_name]
        if not matching_processors.empty:
            df.loc[i, "TDP"] = matching_processors.TDP.iloc[0]

    df[df.TDP.isna()]

    return df

def make_tdp_and_architecture(df_original):
    df = df_original.copy()

    cpus = pd.DataFrame(columns=["ModelNumber", "TDP", "Architecture"])

    urls = {
        "opteron" : "https://en.wikipedia.org/wiki/List_of_AMD_Opteron_processors",
        "core" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Core-based)",
        "nehalem" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Nehalem-based)",
        "sandybridge" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Sandy_Bridge-based)",
        "ivybridge" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Ivy_Bridge-based)",
        "haswell" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Haswell-based)",
        "broadwell" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Broadwell-based)",
        "skylake" :"https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Skylake-based)",
        "kabylabe" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Kaby_Lake-based)",
        "coffeelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Coffee_Lake-based)",
        "cascadelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Cascade_Lake-based)",
        "cometlake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Comet_Lake-based)",
        "icelake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Ice_Lake-based)",
        "rocketlake" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(Rocket_Lake-based)",
        "tigerlake" : "https://en.wikipedia.org/wiki/Tiger_Lake#List_of_Tiger_Lake_CPUs",
        "epyc" : "https://en.wikipedia.org/wiki/Epyc",
        "cooperlake" : "https://en.wikipedia.org/wiki/Cooper_Lake_(microprocessor)#List_of_Cooper_Lake_processors",
        "netburst" : "https://en.wikipedia.org/wiki/List_of_Intel_Xeon_processors_(NetBurst-based)",
    }

    for architecture in urls.keys():
        print(architecture)
        tables = pd.read_html(urls[architecture])

        for table in tables:

            # normalize different header names
            table = table.rename({'Model number': 'ModelNumber', 'TDP(W)': 'TDP'}, axis=1)
            table = table.rename({'Modelnumber': 'ModelNumber', 'TDP (W)': 'TDP'}, axis=1)
            table = table.rename({'Model': 'ModelNumber'}, axis=1)
            table = table.rename({'Modelnumber[7]': 'ModelNumber'}, axis=1)

            table["Architecture"] = architecture # Add static column

            if 'ModelNumber' in table.columns:
                table.columns = table.columns.get_level_values(0)
                # print("Found Table", table.iloc[0], table.columns)
                cpus = pd.concat([table.loc[:, ["ModelNumber", "TDP", "Architecture"]], cpus], ignore_index=True, axis=0, join="outer")

    # Remove header columns where ModelNumber = TDP
    cpus = cpus.drop(cpus[cpus.ModelNumber == cpus.TDP].index)

    cpus_save = cpus.copy()
    cpus = cpus_save.copy()



    cpus[cpus.TDP.astype(str).str.contains(",")] # DEBUG
    cpus[cpus.ModelNumber.astype(str).str.contains(r"\[",regex=True)].to_dict() # DEBUG


    # Unique replacements without pattern
    cpus.TDP = cpus.TDP.str.replace("^80,20W$", "80", regex=True)
    cpus.TDP = cpus.TDP.str.replace("^\s*80\s*,\s*120\s*W$", "120", regex=True)
    cpus.TDP = cpus.TDP.str.replace("^\s*150\s*,\s*120\s*W$", "150", regex=True)
    cpus.TDP = cpus.TDP.str.replace("^92.6 68$", "92.6", regex=True)

    # Replacements with spotted pattern
    cpus.TDP = cpus.TDP.str.replace("^\s*\d+\s*/(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace("^\s*\d+\s*W\s*(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace("^\s*\d+\s*-\s*(\d+)\s*W\s*$", r"\1",regex=True)
    cpus.TDP = cpus.TDP.str.replace("^\s*\d+\s*–\s*(\d+)\s*\s*$", r"\1",regex=True) # Note this is a UTF-8 hyphen!


    #replace weird bracketing, but only for 24 knowns
    assert cpus[cpus.ModelNumber.astype(str).str.contains(r"\[",regex=True)].shape[0] == 24, "More than 24 brackets in ModelNumber. Please manually verify that new ones are also OK"
    cpus.ModelNumber = cpus.ModelNumber.str.replace("\[\d*\]", "",regex=True)


    # normalizing
    cpus.ModelNumber = cpus.ModelNumber.str.replace("\s*", "",regex=True).str.lower()
    cpus.TDP = cpus.TDP.str.replace("\s*W\s*", "",regex=True, flags=re.IGNORECASE)

    unknown_cpus_selector = cpus.TDP.astype(str).str.contains("?", regex=False)
    assert cpus.loc[unknown_cpus_selector].shape[0] == 2, f"More than two unknown processors with ? in TDP found: {cpus.loc[unknown_cpus_selector]}"
    cpus = cpus.drop(cpus[unknown_cpus_selector].index, axis=0)


    assert cpus.ModelNumber.isna().sum() == 0, "ModelNumber contained more than 0 NAs!"
    assert cpus.TDP.isna().sum() == 10, f"TDPcontained more than 10 NAs: {cpus[cpus.TDP.isna()]}" # 10 NA is ok

    # For these 10 the TDP we just don't have ...
    cpus = cpus.dropna()


    cpus.TDP = cpus.TDP.astype(float)


    # Fix the known processors where we have confilicting values by setting to the highes
    # TDP value we know
    cpus["TDP"] = cpus.groupby(["ModelNumber"]).transform(max).TDP
    # now remove the duplicates
    cpus = cpus.drop_duplicates(subset=["ModelNumber"])

    clean_names = df.CPUName.str.replace(r"opteron", "", regex=True)
    for i, clean_name in clean_names.iteritems():
        if cpus[cpus.ModelNumber == clean_name].empty:
            print("No match for", clean_name)
            continue
        found = cpus[cpus.ModelNumber == clean_name]
        assert len(found) < 2, f"Found multiple architectures: {cpus[cpus.ModelNumber == clean_name]}"

        df.loc[i,'TDP'] = found.iloc[0].TDP # Insert TDP in any case

        if df.loc[i,'Architecture'] is not None: # Check before overwriting architecture
            if df.loc[i,'Architecture'] in ['epyc-gen3', 'epyc-gen1', 'epyc-gen2']: continue # allow these, since they provide more info
            assert df.loc[i,'Architecture'] == found.iloc[0].Architecture, f"Previous architecture was {df.loc[i,'Architecture']}. New found is: {found.iloc[0].Architecture}"
        else:
            df.loc[i,'Architecture'] = found.iloc[0].Architecture


    return df

def main():
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 20)
    pd.set_option('display.max_colwidth', None)

    df = pd.read_csv("./../data/spec_data.csv", sep="|", index_col=False, na_values=["None"])

    # Hashing cause we want to identify columns later on based on initial uniqueness
    df['hash'] = pd.util.hash_pandas_object(df)
    #assert(df.hash.nunique() == df.shape[0]) # no duplicate hashes

    ## Cleaning

    helper.visual_check(df.dtypes.to_dict(), "Are all data types ok?")

    df = remove_unneeded_columns(df)

    df["Hardware Availability Month"] = df["Hardware Availability"].str.split("-", expand=True)[0]
    df["Hardware Availability Year"] = df["Hardware Availability"].str.split("-", expand=True)[1]

    df = split_hardware_availabilty(df)

    df = create_cpu_make(df)

    df = create_cpu_name(df)

    df = create_turbo_boost(df)

    df = make_cpu_cores(df)
    df = make_cpu_chips(df)

    df = make_hardware_threads(df)

    df = split_psu(df)

    df = make_cpu_family(df)

    df = make_l2_cache(df)

    df = make_l3_cache(df)

    df = make_architecture_old(df)

    df = make_tdp_and_architecture(df)

    df["AvgPower"] = df.loc[:,['100_AvgPower', '90_AvgPower', '80_AvgPower', '70_AvgPower',
           '60_AvgPower', '50_AvgPower', '40_AvgPower', '30_AvgPower',
           '20_AvgPower', '10_AvgPower', 'ActiveIdle']].mean(axis=1)

    df.to_csv("./../data/spec_data_cleaned_unmelted.csv")

    df = df.drop("AvgPower", axis=1)

    df = melt_power_and_load(df) # spread columns to rows
    df = clean_power_and_load(df) # move 100_AvgPower => 100 as int

    df.to_csv("./../data/spec_data_cleaned.csv")

    '''
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



    # TODO: HW_Vendor
    # just basic cleaning, standardize how companies are written
    # etc.
    vendors = df.loc[df['HW_Vendor'].str.contains('Hewlett'), 'HW_Vendor'].unique()
    #df.HW_Vendor = df.HW_Vendor.str.replace('HEPYCEPYCewlett\s?-?\s?Packard\s?(Enterprise|Company)', '', regex=True, case=False)
    '''






    # test code
    # a_archs_t = pd.DataFrame({'XeonPeon':['CoolProcessorWon 1234', 'CoolProcessorToo 4321', None, None],'OptimusPrime':[None, None, 'CoolProcessorTree', 'CoolProcessorFore'],})
    # a_df_t = pd.DataFrame({'CPU': ['CoolProcessorWon 1234', 'Totally Not In DataSet','CoolProcessorWon', 'CoolProcessorFore', 'CoolProcessor']})
    # a_t = a_df_t.CPU.isin(a_archs_t.XeonPeon)

    ## Disk Drive, size + type (SSD or HDD)






if __name__ == "__main__":
    main()
