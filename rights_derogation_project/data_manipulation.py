import pandas as pd
import os

from rights import rights, cleaned_rights

# column_dtypes = {'CountryName', 'CountryCode', 'RegionName', 'RegionCode', 'Jurisdiction', 'Date', }

data = pd.read_csv('data/OxCGRT_latest.csv', dtype=str).reset_index()

data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d').dt.date

data['ConfirmedCases'] = pd.to_numeric(data['ConfirmedCases'])

countries = data['CountryName'].unique()

countries = list(filter(None, countries))
countries = [x for x in countries if str(x) != 'nan']

def collect_rights_data(data, country, rights, cleaned_rights):
    countries = [country]
    rights_list = []
    start_dates = []
    end_dates = []
    derogation_levels = []
    cases_list = []

    for right in rights:
        current_level = 0
        right_df = data[['Date', right, 'ConfirmedCases']].reset_index()
        right_df.sort_values(by = ['Date'], inplace = True)
        right_df.fillna(0, inplace = True)
        right_df[right] = pd.to_numeric(right_df[right])
        starting_cases = 0
        for index, row in right_df.iterrows():
            if row[right] != current_level:
                if current_level > 0:
                    ending_cases = right_df.iloc[index-1]['ConfirmedCases']
                    case_change = ending_cases - starting_cases
                    cases_list.append(case_change)
                    end_date = right_df.iloc[index-1]['Date']
                    end_dates.append(end_date)
                current_level = row[right]
                if current_level > 0:
                    rights_list.append(cleaned_rights[right])
                    start_dates.append(row['Date'])
                    derogation_levels.append(current_level)
                    starting_cases = row['ConfirmedCases']
        if current_level > 0:
            end_date = right_df.iloc[-1]['Date']
            end_dates.append(end_date)
            ending_cases = right_df.iloc[index-1]['ConfirmedCases']
            case_change = ending_cases - starting_cases
            cases_list.append(case_change)
    
    countries = countries * len(rights_list)

    results = pd.DataFrame(list(zip(countries, rights_list, start_dates, end_dates, derogation_levels, cases_list)), columns = ['Country', 'Right', 'Start Date', 'End Date', 'Derogation Level', 'Confirmed Cases'])
    results.sort_values(by = ['Right', 'Start Date'], inplace=True)
    return results

# portugal = country_data = data.loc[data['CountryName'] == 'Portugal']

# portugal_results = collect_rights_data(portugal, 'Portugal', rights = rights, cleaned_rights = cleaned_rights)

# portugal_results.to_csv('portugal_results.csv')

path = 'output_files/'

for country in countries:
    print('Processing: ', country)
    country_data = data.loc[data['CountryName'] == country]
    if len(country_data['RegionName'].unique()) > 1: # if a country has states
        new_path = path + country.lower()
        if not os.path.exists(new_path): # we need to make a folder for the country's states
            os.makedirs(new_path)
        states = country_data['RegionName'].unique()
        states = list(filter(None, states))
        states = [x for x in states if str(x) != 'nan']
        for state in states:
            print('Processing state in ', country, ': ', state)
            output_path = new_path + '/' + state.lower() + '_results.csv'
            state_data = country_data.loc[country_data['RegionName'] == state]
            state_results = collect_rights_data(state_data, state, rights = rights, cleaned_rights = cleaned_rights)
            state_results.to_csv(output_path)
    else:
        output_path = path + country.lower() + '_results.csv'
        country_results = collect_rights_data(country_data, country, rights = rights, cleaned_rights = cleaned_rights)
        country_results.to_csv(output_path)