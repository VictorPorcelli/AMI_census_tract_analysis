#!/usr/bin/env python
# coding: utf-8

# Research Question: How do minimum income requirements in given areas compare to local median incomes? (Links to dataset sources found below)
# 
# Housing New York: https://data.cityofnewyork.us/Housing-Development/Housing-New-York-Units-by-Building/hg8x-zxpr
# 
# Census tract data was downloaded from https://data.census.gov. The codes for the data used were S1903 for median income and B11016 for family size, both using ACS 5-year estimates 2019 data.

# In[1]:


#get_ipython().system('pip install pandas')
import pandas as pd
import requests


# Load the Housing New York dataset

# In[2]:


housing_data = pd.read_csv("./Housing_New_York_Units_by_Building.csv")
housing_data.head()


# Load the census median income dataset, with income in 2019 dollars

# In[3]:


income_data = pd.read_csv("./ACS5YR2019_median_income.csv")
income_data.head()


# Load the census family size dataset.

# In[4]:


family_data = pd.read_csv("./ACSDT5Y2019_family_size.csv")
family_data.head()


# Since census tract is the main unit of interest, try to fill in any missing census tracts in the Housing New York data using other location information where possible.

# In[5]:


#get_ipython().system('pip install censusgeocode')
import censusgeocode as cg

print(housing_data['Census Tract'].isna().sum())

def tract_filler(row):
    tract = row['Census Tract']
    
    if tract == "" or tract == 'Not Found':
        if (row['Latitude'] != float('NaN')) and (row['Longitude'] != float('NaN')):
            try:
                response = cg.coordinates(x = row['Longitude'], y = row['Latitude'], returntype = 'geographies', timeout = 3)
                tract = str(response['Census Tracts'][0]['TRACT'])
            except:
                pass

        elif (row['Number'].isna() == False) and (row['Street'].isna() == False):
            boro = str(row['Borough']).strip()
            if boro.find("Manhattan") != -1:
                boro = "New York"
            address = row['Number'].strip()+", "+boro+", NY"
            try:
                response = cg.onelineaddress(address, returntype = 'geographies', timeout = 3)
                tract = str(response[0]['geographies']['Census Tracts'][0]['TRACT'])
            except:
                pass

        tract = str(tract)
        if len(tract) < 5:
            tract = row['Census Tract']
    
    return tract

housing_data['Census Tract'] = housing_data.apply(tract_filler, axis = 1)
print(housing_data['Census Tract'].isna().sum())

#Turns out, there are no observations which are missing census tracts but not other important location information!
#delete missing census tracts

housing_data = housing_data[housing_data['Census Tract'].isna() == False]
print(housing_data['Census Tract'].isna().sum())


# Reformat census tracts to be uniform across the three datasets. Start with the two census datasets.

# In[6]:


def census_reformat(row):
    if row['NAME'].find('Geographic') == -1:
        split_str = row['NAME'].split(",")
        boro = split_str[1].strip()
        full_code = str(row['GEO_ID'])
        num = full_code[14:18]+"."+full_code[18:]
        if boro.upper() =='BRONX COUNTY':
            tract_name = "BX"+num
        elif boro.upper() == 'QUEENS COUNTY':
            tract_name = "Q"+num
        elif boro.upper() == 'NEW YORK COUNTY':
            tract_name = "M"+num
        elif boro.upper() == 'RICHMOND COUNTY':
            tract_name = "SI"+num
        elif boro.upper() == 'KINGS COUNTY':
            tract_name = "BK"+num
        return tract_name
    else:
        return row['GEO_ID']

income_data['GEO_ID'] = income_data.apply(census_reformat, axis = 1)

#Change the name of the series to be the same as in the housing dataset
income_data.insert(0, 'Census Tract', income_data['GEO_ID'])
del income_data['GEO_ID']

#Also, delete the first row
income_data = income_data.iloc[1: , :]
income_data


# In[7]:


family_data['GEO_ID'] = family_data.apply(census_reformat, axis = 1)

#Change the name of the series to be the same as in the housing dataset
family_data.insert(0, 'Census Tract', family_data['GEO_ID'])
del family_data['GEO_ID']

#Also, delete the first row
family_data = family_data.iloc[1: , :]
family_data


# Now reformat the housing dataset to mirror the census one. For the housing dataset, the census tract value wasn't always clean as, for example, tract 177.02 was input as 17702. However, city census tracts also do not go above 4 digits or below 1 digit. So, if the value is 1-2 digits or 5-6 digits this is not an issue. Additionally, for those 3-4 digits, additional census tract designations appear to only be in the format of zere followed by a non-zero value. So, for those cases where this is the case fill in the census tract using an API call.

# In[9]:


def housing_reformat(row):
    good = True
    try:
        int(row['Census Tract'])
    except:
        good = False
    if good:
        tract = str(row['Census Tract']).strip()
        num = ""
        if len(tract) == 1:
            num = "000"+tract+".00"
        elif len(tract) == 2:
            num = "00"+tract+".00"
        elif len(tract) == 3:
            if (tract[1] != '0') or (tract[2] == '0'):
                num = "0"+tract+".00"
            else:
                try:
                    response = cg.coordinates(x = row['Longitude'], y = row['Latitude'], returntype = 'geographies', timeout = 3)
                    num = str(response['Census Tracts'][0]['TRACT'])
                    num = num[0:4]+"."+num[4:]
                except:
                    pass
        elif len(tract) == 4:
            if (tract[2] != '0') or (tract[3] == '0'):
                num = tract+".00"
            else:
                try:
                    response = cg.coordinates(x = row['Longitude'], y = row['Latitude'], returntype = 'geographies', timeout = 3)
                    num = str(response['Census Tracts'][0]['TRACT'])
                    num = num[0:4]+"."+num[4:]
                except:
                    pass
        elif len(tract) == 5:
            num = "0"+tract
            num = num[0:4]+"."+num[4:]
        elif len(tract) == 6:
            num = tract
            num = num[0:4]+"."+num[4:]
                 
        boro = str(row['Borough']).strip()
        if boro.upper() =='BRONX':
            tract_name = "BX"+num
        elif boro.upper() == 'QUEENS':
            tract_name = "Q"+num
        elif boro.upper() == 'MANHATTAN':
            tract_name = "M"+num
        elif boro.upper() == 'STATEN ISLAND':
            tract_name = "SI"+num
        elif boro.upper() == 'BROOKLYN':
            tract_name = "BK"+num
            
        return tract_name
    else:
        return row['Census Tract']
    
housing_data['Census Tract'] = housing_data.apply(housing_reformat, axis = 1)
housing_data['Census Tract']


# Next, combine the datasets compiling all of the relevant information (median income, household size, and affordable housing units) for each census tract. First, clean up the census datasets to only include key information and have better series names.

# In[10]:


income_data = income_data[['Census Tract', 'S1903_C03_024E', 'S1903_C03_025E', 'S1903_C03_026E', 'S1903_C03_027E', 'S1903_C03_028E', 'S1903_C03_029E', 'S1903_C03_034E']]
income_data = income_data.rename(columns={'S1903_C03_024E': 'med_inc_family_2', 'S1903_C03_025E': 'med_inc_family_3', 'S1903_C03_026E': 'med_inc_family_4', 'S1903_C03_027E': 'med_inc_family_5', 'S1903_C03_028E': 'med_inc_family_6', 'S1903_C03_029E': 'med_inc_family_7', 'S1903_C03_034E': 'med_inc_nonfamily'})

income_data.head()


# In[11]:


family_data = family_data[['Census Tract', 'B11016_001E', 'B11016_003E', 'B11016_004E', 'B11016_005E', 'B11016_006E', 'B11016_007E', 'B11016_008E', 'B11016_009E']]
family_data = family_data.rename(columns={'B11016_001E': 'total_hh', 'B11016_003E': 'two_person_hh', 'B11016_004E': 'three_person_hh', 'B11016_005E': 'four_person_hh', 'B11016_006E': 'five_person_hh', 'B11016_007E': 'six_person_hh', 'B11016_008E': 'sev_person_hh', 'B11016_009E': 'nonfamily_hh'})

family_data.head()


# Next, take the important series from the housing data and add it to a new dataframe.

# In[12]:


#Make a new dataset of all the census tracts
combined_data = pd.DataFrame(income_data['Census Tract'])

#add the various unit types
temp_series = housing_data.groupby('Census Tract')['Extremely Low Income Units'].sum()
combined_data = pd.merge(combined_data, temp_series, on = "Census Tract")

temp_series = housing_data.groupby('Census Tract')['Very Low Income Units'].sum()
combined_data = pd.merge(combined_data, temp_series, on = "Census Tract")

temp_series = housing_data.groupby('Census Tract')['Low Income Units'].sum()
combined_data = pd.merge(combined_data, temp_series, on = "Census Tract")

temp_series = housing_data.groupby('Census Tract')['Moderate Income Units'].sum()
combined_data = pd.merge(combined_data, temp_series, on = "Census Tract")

temp_series = housing_data.groupby('Census Tract')['Middle Income Units'].sum()
combined_data = pd.merge(combined_data, temp_series, on = "Census Tract")

combined_data


# Create a function to find the mode affordability designation and add a new series which stores it. (Note: this function will take the higher income designation if there is a tie.)

# In[13]:


def find_mode_unit(row):
    max_value = row[['Extremely Low Income Units', 'Very Low Income Units', 'Low Income Units', 'Moderate Income Units', 'Middle Income Units']].max()
    mode_series = "no affordable units"
    
    if max_value > 0:
        index = row.index
        x = 0
        for i in row:
            if i == max_value:
                mode_series = index[x]
            x+=1
    return mode_series
    
combined_data['mode_unit'] = combined_data.apply(find_mode_unit, axis = 1)
combined_data


# Create a function to find the mode family size and add a new series which stores it. 

# In[14]:


def find_mode_family(row):
    max_value = row[['two_person_hh', 'three_person_hh', 'four_person_hh', 'five_person_hh', 'six_person_hh', 'sev_person_hh']].max()
    mode_series = ""
    index = row.index
    x = 0
    for i in row:
        if i == max_value:
            mode_series = index[x]
        x+=1
    return mode_series
    
family_data['mode_family'] = family_data.apply(find_mode_family, axis = 1)
family_data


# Convert family size data into percentages to use for a weighted average calculation later.

# In[15]:


def pct_converter(row):
    percentages = []
    
    percentages.append(row['two_person_hh'])
    percentages.append(row['three_person_hh'])
    percentages.append(row['four_person_hh'])
    percentages.append(row['five_person_hh'])
    percentages.append(row['six_person_hh'])
    percentages.append(row['sev_person_hh'])
    percentages.append(row['nonfamily_hh'])
    
    try:
        total = int(row['total_hh'])
    except:
        pass
    if total > 0:
        
        percentages.clear()
        percentages.append(int(row['two_person_hh'])/total)
        percentages.append(int(row['three_person_hh'])/total)
        percentages.append(int(row['four_person_hh'])/total)
        percentages.append(int(row['five_person_hh'])/total)
        percentages.append(int(row['six_person_hh'])/total)
        percentages.append(int(row['sev_person_hh'])/total)
        percentages.append(int(row['nonfamily_hh'])/total)
        
    return pd.Series(percentages)
    
family_data[['two_person_hh', 'three_person_hh', 'four_person_hh', 'five_person_hh', 'six_person_hh', 'sev_person_hh','nonfamily_hh']] = family_data.apply(pct_converter, axis = 1)
family_data


# Set up seperate datasets for the imputing process later (details below).

# In[16]:


def rem_boro(row):
    census_str = row['Census Tract']
    census_str = census_str[len(census_str)-7:len(census_str)-1]
    return float(census_str)

def add_boro(row):
    if row['Census Tract'].find("B") == -1 and row['Census Tract'].find("S") == -1:
        return row['Census Tract'][0]
    else:
        return row['Census Tract'][0:2]

#first, add a column with census tract as a float and no borough code
income_data['Tract No Code'] = income_data.apply(rem_boro, axis = 1)

#add a borough column for convenience
income_data['Boro'] = income_data.apply(add_boro, axis = 1)

bronx_inc = income_data[income_data['Boro'] == 'BX']
queens_inc = income_data[income_data['Boro'] == 'Q']
man_inc = income_data[income_data['Boro'] == 'M']
staten_inc = income_data[income_data['Boro'] == 'SI']
bklyn_inc = income_data[income_data['Boro'] == 'BK']


# For key missing income variables, impute using an average of the values for the nearest two census tracts. Since there is already some housing data missing values, it is important to try and make use of as much of the data available. The census data is much more rich, and much of it is not being used since there are only so many census tracts with affordable housing units. Looking at neighborhing census tracts should be a viable way of imputing these variables.

# In[17]:


def float_converter(string):
    string = string.replace(",","")
    string = string.replace("+","")
    try:
        flt = float(string)
    except:
        flt = 250000.00
    return flt

#Make a function to impute values
def impute_inc(row):
    new_row = []
    new_row.append(row['med_inc_family_2'])
    new_row.append(row['med_inc_family_3'])
    new_row.append(row['med_inc_family_4'])
    new_row.append(row['med_inc_family_5'])
    new_row.append(row['med_inc_family_6'])
    new_row.append(row['med_inc_family_7'])
    new_row.append(row['med_inc_nonfamily'])
    #if housing_data['Census Tract'].str.contains(row['Census Tract']):
    col_names = ['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']
    #first, identify missing values
    missing_vals = []
    inc_vals = row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]
    x = 0
    for val in inc_vals:
        if str(val).find("-") != -1:
            missing_vals.append(x)
        x+=1

    if len(missing_vals) > 0:
        #search in the corresponding dataframe for nearrest census tract
        tract = row['Census Tract']
        if tract.find("BX") != -1:
            tract = float(row['Census Tract'][len(row['Census Tract'])-7:len(row['Census Tract'])])
            ct_list = pd.Series(bronx_inc['Tract No Code'])
            min_diff = [999.99,999.99]
            comparison_ct = [0,0]
            for index, ct in ct_list.items():
                diff = abs(ct - tract)
                if diff < min_diff[0]:
                    temp_row = bronx_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[0] = diff
                        comparison_ct[0] = index
                elif diff < min_diff[1]:
                    temp_row = bronx_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]
                    
                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[1] = diff
                        comparison_ct[1] = index
            
            if comparison_ct[0] != 0 and comparison_ct[1] != 0:
                row1 = bronx_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                row2 = bronx_inc.loc[[comparison_ct[1]]]
                row2 = row2[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    inc2_fl = float_converter(row2[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
                    z+=1
            elif comparison_ct[0] != 0:
                row1 = bronx_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append(inc1_fl)
                    z+=1
            else:
                imputed_vals = inc_vals
            y = 0
            new_row.clear()
            for i in inc_vals:
                if y in missing_vals:
                    new_row.append(imputed_vals[missing_vals.index(y)])
                else:
                    new_row.append(i)
                y += 1

        elif tract.find("Q") != -1:
            tract = float(row['Census Tract'][len(row['Census Tract'])-7:len(row['Census Tract'])])
            ct_list = pd.Series(queens_inc['Tract No Code'])
            min_diff = [999.99,999.99]
            comparison_ct = [0,0]
            for index, ct in ct_list.items():
                diff = abs(ct - tract)
                if diff < min_diff[0]:
                    temp_row = queens_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[0] = diff
                        comparison_ct[0] = index
                elif diff < min_diff[1]:
                    temp_row = queens_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[1] = diff
                        comparison_ct[1] = index
            
            if comparison_ct[0] != 0 and comparison_ct[1] != 0:
                row1 = queens_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                row2 = queens_inc.loc[[comparison_ct[1]]]
                row2 = row2[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    inc2_fl = float_converter(row2[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
                    z+=1
            elif comparison_ct[0] != 0:
                row1 = queens_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append(inc1_fl)
                    z+=1
            else:
                imputed_vals = inc_vals
                
            y = 0
            new_row.clear()
            for i in inc_vals:
                if y in missing_vals:
                    new_row.append(imputed_vals[missing_vals.index(y)])
                else:
                    new_row.append(i)
                y += 1

        elif tract.find("M") != -1:
            tract = float(row['Census Tract'][len(row['Census Tract'])-7:len(row['Census Tract'])])
            ct_list = pd.Series(man_inc['Tract No Code'])
            min_diff = [999.99,999.99]
            comparison_ct = [0,0]
            for index, ct in ct_list.items():
                diff = abs(ct - tract)
                if diff < min_diff[0]:
                    temp_row = man_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[0] = diff
                        comparison_ct[0] = index
                elif diff < min_diff[1]:
                    temp_row = man_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[1] = diff
                        comparison_ct[1] = index
            
            if comparison_ct[0] != 0 and comparison_ct[1] != 0:
                row1 = man_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                row2 = man_inc.loc[[comparison_ct[1]]]
                row2 = row2[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    inc2_fl = float_converter(row2[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
                    z+=1
            elif comparison_ct[0] != 0:
                row1 = man_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append(inc1_fl)
                    z+=1
            else:
                imputed_vals = inc_vals
                
            y = 0
            new_row.clear()
            for i in inc_vals:
                if y in missing_vals:
                    new_row.append(imputed_vals[missing_vals.index(y)])
                else:
                    new_row.append(i)
                y += 1

        elif tract.find("SI") != -1:
            tract = float(row['Census Tract'][len(row['Census Tract'])-7:len(row['Census Tract'])])
            ct_list = pd.Series(staten_inc['Tract No Code'])
            min_diff = [999.99,999.99]
            comparison_ct = [0,0]
            for index, ct in ct_list.items():
                diff = abs(ct - tract)
                if diff < min_diff[0]:
                    temp_row = staten_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[0] = diff
                        comparison_ct[0] = index
                elif diff < min_diff[1]:
                    temp_row = staten_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[1] = diff
                        comparison_ct[1] = index
            
            if comparison_ct[0] != 0 and comparison_ct[1] != 0:
                row1 = staten_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                row2 = staten_inc.loc[[comparison_ct[1]]]
                row2 = row2[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    inc2_fl = float_converter(row2[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
                    z+=1
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
            elif comparison_ct[0] != 0:
                row1 = staten_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append(inc1_fl)
                    z+=1
            else:
                imputed_vals = inc_vals
                
            y = 0
            new_row.clear()
            for i in inc_vals:
                if y in missing_vals:
                    new_row.append(imputed_vals[missing_vals.index(y)])
                else:
                    new_row.append(i)
                y += 1

        elif tract.find("BK") != -1:
            tract = float(row['Census Tract'][len(row['Census Tract'])-7:len(row['Census Tract'])])
            ct_list = pd.Series(bklyn_inc['Tract No Code'])
            min_diff = [999.99,999.99]
            comparison_ct = [0,0]
            for index, ct in ct_list.items():
                diff = abs(ct - tract)
                if diff < min_diff[0]:
                    temp_row = bklyn_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[0] = diff
                        comparison_ct[0] = index
                elif diff < min_diff[1]:
                    temp_row = bklyn_inc.loc[[index]]
                    temp_row = temp_row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                    add = True
                    z = 0
                    for i in temp_row:
                        if (str(temp_row[i]).find("-") != -1) and (z in missing_vals):
                            add = False
                        z+=1

                    if add:
                        min_diff[1] = diff
                        comparison_ct[1] = index
            
            if comparison_ct[0] != 0 and comparison_ct[1] != 0:
                row1 = bklyn_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                row2 = bklyn_inc.loc[[comparison_ct[1]]]
                row2 = row2[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    inc2_fl = float_converter(row2[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append((inc1_fl+inc2_fl)/2)
                    z+=1
            elif comparison_ct[0] != 0:
                row1 = bklyn_inc.loc[[comparison_ct[0]]]
                row1 = row1[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']]

                imputed_vals = []
                z = 0
                for i in missing_vals:
                    inc1_fl = float_converter(row1[col_names[missing_vals[z]]].str)
                    
                    imputed_vals.append(inc1_fl)
                    z+=1
            else:
                imputed_vals = inc_vals
                
            y = 0
            new_row.clear()
            for i in inc_vals:
                if y in missing_vals:
                    new_row.append(imputed_vals[missing_vals.index(y)])
                else:
                    new_row.append(i)
                y += 1
    
    return pd.Series(new_row)

income_data_imputed = income_data[income_data['Census Tract'].isin(housing_data['Census Tract'])]
income_data_imputed[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']] = income_data_imputed.apply(impute_inc, axis = 1)
income_data_imputed


# Combine the datasets.

# In[18]:


combined_data = pd.merge(combined_data, family_data, on = "Census Tract")
combined_data = pd.merge(combined_data, income_data_imputed, on = "Census Tract")
combined_data


# Compute the difference between mode affordability designation minimum income requirement for the mode family size and the mode family size median income. AMI levels for 2019, which will be used in this analysis, can be found here: https://www.safeguardcredit.org/wp-content/uploads/2020/02/AMI_Safeguard.pdf. For households with 7+ individuals an average of the minimum income requirement for 7 and 8 person households will be used.

# In[71]:


ami_levels = [74700, 85400, 96100, 106700, 115300, 123800, 136650]
pct_ami = [0, 0.31, 0.51, 0.81, 1.20]

def calc_mode_diff(row):
    mode_fam = row["mode_family"]
    mode_unit = row["mode_unit"]
    
    #get ami level
    if mode_fam == "nonfamily_hh":
        level_index = 0
    elif mode_fam == "two_person_hh":
        level_index = 1
    elif mode_fam == "three_person_hh":
        level_index = 2
    elif mode_fam == "four_person_hh":
        level_index = 3
    elif mode_fam == "five_person_hh":
        level_index = 4
    elif mode_fam == "six_person_hh":
        level_index = 5
    elif mode_fam == "sev_person_hh":
        level_index = 6
        
    #get pct ami
    if mode_unit == "Extremely Low Income Units":
        pct_index = 0
    elif mode_unit == "Very Low Income Units":
        pct_index = 1
    elif mode_unit == "Low Income Units":
        pct_index = 2
    elif mode_unit == "Moderate Income Units":
        pct_index = 3
    elif mode_unit == "Middle Income Units":
        pct_index = 4
    elif mode_unit == "no affordable units":
        return float('NaN')
        
    inc_levels = list(row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']])
        
    if level_index == 0:
        med_inc = float(row['med_inc_nonfamily'])
    else:
        try:
            med_inc = float(inc_levels[level_index-1])
        except:
            med_inc = 250000.00
            
    if pct_index == 0:
        return med_inc
    else:
        min_inc = pct_ami[pct_index] * ami_levels[level_index]
        return (med_inc - min_inc)

combined_data['mode_diff'] = combined_data.apply(calc_mode_diff, axis = 1)
combined_data


# Compute a weighted average difference among different family sizes.

# In[53]:


def calc_weighted_avg(row):
    mode_unit = row["mode_unit"]
    
    #get pct ami
    if mode_unit == "Extremely Low Income Units":
        pct_index = 0
    elif mode_unit == "Very Low Income Units":
        pct_index = 1
    elif mode_unit == "Low Income Units":
        pct_index = 2
    elif mode_unit == "Moderate Income Units":
        pct_index = 3
    elif mode_unit == "Middle Income Units":
        pct_index = 4
    elif mode_unit == "no affordable units":
        return float('NaN')
    
    weighted_avg = 0.00
    inc_levels = list(row[['med_inc_family_2', 'med_inc_family_3', 'med_inc_family_4', 'med_inc_family_5', 'med_inc_family_6', 'med_inc_family_7', 'med_inc_nonfamily']])
    fam_sizes = list(row[['two_person_hh', 'three_person_hh', 'four_person_hh', 'five_person_hh', 'six_person_hh', 'sev_person_hh', 'nonfamily_hh']])
    
    for ami in ami_levels:
        if ami_levels.index(ami) == 0:
            weighted_avg += ((float(row['med_inc_nonfamily'])) - (pct_ami[pct_index]*ami)) * float(row['nonfamily_hh'])
        else:
            try:
                weighted_avg += ((float(inc_levels[ami_levels.index(ami)-1])) - (pct_ami[pct_index]*ami)) * float(fam_sizes[ami_levels.index(ami)-1])
            except:
                weighted_avg += ((250000.00) - (pct_ami[pct_index]*ami)) * float(fam_sizes[ami_levels.index(ami)-1])

    return weighted_avg
    
combined_data['weighted_avg'] = combined_data.apply(calc_weighted_avg, axis = 1)
combined_data


# Clean up data to remove those with a null weighted_avg or mode_diff.

# In[72]:


combined_data = combined_data[combined_data['mode_diff'] != float("NaN")]
combined_data = combined_data[combined_data['weighted_avg'] != float("NaN")]


# Now, plot some figures using the various units of analysis. To prepare, we are going to need to know if the two differences of interest are above/below zero.

# In[73]:


combined_data["mode_diff_zero"] = (combined_data['mode_diff'] > 0)
combined_data["avg_diff_zero"] = (combined_data['weighted_avg'] > 0)
combined_data


# Create a bar chart of whether the mode AMI (based on mode affordability designation & family size) is above/below the mode family size median income.

# In[1]:

#First, set up an output folder

import os

if not os.path.exists("graphs"):
    os.makedirs("graphs")

#!pip install plotly
import plotly.express as px
import plotly.io as pio
#pio.renderers.default='notebook'

fig = px.bar(combined_data, x="Boro", color="mode_diff_zero",
             title="Minimum Income Requirement vs Median Income by Borough",
             barmode='group',
             labels={'count':'Number of Units', 'mode_diff_zero':"Requirement < Median Income", 'Boro':'Borough'}
            )

fig.show()

fig.write_image("graphs/bar_modediff.png")

# Create the same chart for the weighted average variable.

# In[97]:


#!pip install plotly
import plotly.express as px

fig = px.bar(combined_data, x="Boro", color="avg_diff_zero",
             title="Minimum Income Requirement vs Median Income by Borough",
             barmode='group',
             labels={'count':'Number of Units', 'avg_diff_zero':"Requirement < Median Income", 'Boro':'Borough'}
            )

fig.show()

fig.write_image("graphs/bar_avgdiff.png")

# Reformat census tracts one more time to match the geojson that will be used.

# In[84]:


def json_format(row):
    tract = str(row['Census Tract']).replace(".","")
    
    if tract.find("M") != -1:
        tract = "1"+tract[1:]
    elif tract.find("BX") != -1:
        tract = "2"+tract[2:]
    elif tract.find("BK") != -1:
        tract = "3"+tract[2:]
    elif tract.find("Q") != -1:
        tract = "4"+tract[1:]
    elif tract.find("SI") != -1:
        tract = "5"+tract[2:]

    return tract

combined_data['Census Tract'] = combined_data.apply(json_format, axis = 1)
combined_data


# Now, create a heatmap.

# In[98]:


geojson_url = 'https://data.cityofnewyork.us/api/geospatial/fxpq-c8ku?method=export&format=GeoJSON'

response = requests.get(geojson_url)
geojson_data = response.json()

fig = px.choropleth_mapbox(combined_data,
                           geojson=geojson_url,
                           locations='Census Tract',
                           featureidkey='properties.boro_ct2010',
                           color= 'mode_diff',
                           range_color=(-10000, 10000),
                           hover_data=['Census Tract'],
                           labels={'mode_diff':'Difference'},
                           title="Difference in Median Income and Minimum Income Requirement",
                           center = {'lat': 40.73, 'lon': -73.98},
                           zoom=9,
                           mapbox_style='carto-positron')

fig.update_layout(height=700)
fig.show()

fig.write_html("graphs/heatmap_modediff.html")

# Now use the weighted average.

# In[99]:


geojson_url = 'https://data.cityofnewyork.us/api/geospatial/fxpq-c8ku?method=export&format=GeoJSON'

response = requests.get(geojson_url)
geojson_data = response.json()

fig = px.choropleth_mapbox(combined_data,
                           geojson=geojson_url,
                           locations='Census Tract',
                           featureidkey='properties.boro_ct2010',
                           color= 'weighted_avg',
                           range_color=(-10000, 10000),
                           hover_data=['Census Tract'],
                           labels={'mode_diff':'Difference'},
                           title="Difference in Median Income and Minimum Income Requirement",
                           center = {'lat': 40.73, 'lon': -73.98},
                           zoom=9,
                           mapbox_style='carto-positron')

fig.update_layout(height=700)
fig.show()

fig.write_html("graphs/heatmap_avgdiff.html")


# Try a color based on only if the difference is 0 or nonzero.

# In[100]:


geojson_url = 'https://data.cityofnewyork.us/api/geospatial/fxpq-c8ku?method=export&format=GeoJSON'

response = requests.get(geojson_url)
geojson_data = response.json()

fig = px.choropleth_mapbox(combined_data,
                           geojson=geojson_url,
                           locations='Census Tract',
                           featureidkey='properties.boro_ct2010',
                           color= 'mode_diff_zero',
                           hover_data=['Census Tract'],
                           labels={'mode_diff_zero':'Median Inc > Minimimum Inc Requirement'},
                           title="Difference in Median Income and Minimum Income Requirement",
                           center = {'lat': 40.73, 'lon': -73.98},
                           zoom=9,
                           mapbox_style='carto-positron')

fig.update_layout(height=700)
fig.show()

fig.write_html("graphs/heatmap_modediff2.html")


# In[101]:


geojson_url = 'https://data.cityofnewyork.us/api/geospatial/fxpq-c8ku?method=export&format=GeoJSON'

response = requests.get(geojson_url)
geojson_data = response.json()

fig = px.choropleth_mapbox(combined_data,
                           geojson=geojson_url,
                           locations='Census Tract',
                           featureidkey='properties.boro_ct2010',
                           color= 'avg_diff_zero',
                           hover_data=['Census Tract'],
                           labels={'avg_diff_zero':'Median Inc > Minimimum Inc Requirement'},
                           title="Difference in Median Income and Minimum Income Requirement",
                           center = {'lat': 40.73, 'lon': -73.98},
                           zoom=9,
                           mapbox_style='carto-positron')

fig.update_layout(height=700)
fig.show()

fig.write_html("graphs/heatmap_avgdiff2.html")

