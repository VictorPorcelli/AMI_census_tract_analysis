# AMI_census_tract_analysis
Analysis of affordable housing minimum income requirements versus median income by census tract.

**Background:**
For a long time, I wanted to do some empirical analysis looking at just how affordable "affordable housing" is in New York City. Affordable housing designations are based on Area Median Income, which is a federal designation encompassing the entire Greater New York area, and so is not very useful at a more granular level. So, NYC uses percentage of AMI to determine affordability designations. These affordability designations (besides the lowest & highest) have a range of incomes they apply to — meaning there is a minimum income and maximum income to qualify for 'x' type of affordable housing unit. AMI also varies based on family size. In past research and reporting I've done, I've noticed that the minimum income requirement for some units appears fairly high, and not necessarily affordable for those in the immediate area. So I set out to test whether or not this is the case and, if it is, how common or uncommon it is.

**What I did:**
Using NYC Open Data on all Housing For New York affordable housing units built since 2014, I compared the minimum income requirements of the most common affordability designation in a given census tract with the median income in said census tract. Essentially, I wanted to answer: are the majority of affordable housing units built in a given area truly affordable for an average person/family who lives there?

I used two modes of analysis. Both used the mode affordability designation for the minimum income requriement calculation.
(1) Used the mode family size to compute the minimum income requirement based on the AMI value for the mode family size and then compared that to the median income of that family size for the given census tract.
(2) Computed a weighted average which compared the minimum income requirement vs the median income for each family size and weighted it based on the proportion of the population of that family size in the given census tract.

**There are three main problems with the datasets used:**
(1) The NYC Open Data dataset on Housing For New York units is missing the census tract information for a decent amount of them, and although I wrote a code that could have used other information to get the census tract, it seems most of those missing their census tract are also missing other key location identifiers.
(2) There is some missing data in the median income dataset I used from the census. To solve this, I imputed data by taking the average of the two nearest census tracts for any missing values. This is definitely an imperfect solution but the only one I could think of.
(3) Census data on family size only goes to 7 while AMI goes to 8.

Due to the above issues, this analysis definitely has some limitations and should not be taken at face value. But it is still an intersting and useful exercise, and if I do find the time to obtain more complete data the code could provide much more robust insights into the central question.
