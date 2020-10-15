'''
This script takes a .csv file with an address column and returns a file to be input
into the Census geocoder.

The census file is a .csv file with an index column, a street address column, a city
column, a state column, and a zip code column.

This script uses the usaddress library to split the input address into pieces.
This is done in parse_address(). parse_address() then chooses the pieces that are
relevant to the Census geocoder. We only want the street number, street name, city,
state, and zip code.

get_city_name() looks up potential city names in a city name table to identify the
most likely city name for a particular address.

get_census_batch() prepares the input file for the Census geocoder.
It takes the results from parsing the address and puts them into the
columns the Census geocoder wants. Finally, it exports that table as a .csv.
'''

# Import packages
import pandas as pd
import usaddress
import re

class AddressParser():

    def __init__(self, filename, cities_db_filename, column_name='address', output_filename='census_batch.csv'):
        self.filename = filename
        self.column_name = column_name
        self.output_filename = output_filename

        self.cities_db = pd.read_csv(cities_db_filename)

        dataset = pd.read_csv(filename)
        dataset = dataset.dropna(axis=0, subset=[column_name])
        self.addresses = dataset[column_name]

        self.get_census_batch(self.addresses)
    
    def get_city_name(self, parsed_address):
        '''
        This function looks up city name to identify the most likely city name for a particular address.
        The cities_db table has, ideally, all potential cities in a U.S. mailing address.
        This function tries all remaining potential pieces of the address (zip code and state have already
        been taken out by now).
        For example, if we still have ['1234', 'Main', 'St', 'Memphis'], this function will search for
        '1234 Main St Memphis' in the table first, then 'Main St Memphis', then 'St Memphis', and finally
        'Memphis'. In this case, 'Memphis' will probably be the only one that finds a match in the table,
        so this function will return 'Memphis' as the city name.
        If 'St Memphis' had been found in the cities_db table, 'St Memphis' would have been returned as the
        city name.

        The line 'city_name = city_name.translate({ord('{'):None, ord('}'):None, ord('('):None, ord(')'):None, ord('['):None, ord(']'):None})'
        removes any parentheses or square or curly brackets from the city name.
        This is because an open parenthesis in the city name will cause an error in str.contains().

        This function also returns an int variable remaining_len that tells parse_address how many pieces
        to remove from the address. If the city name is two words, for example, remaining_len will equal the 
        address length - 2.
        '''
        found_city = False
        remaining_len = -1
        while found_city == False:
            city_name = ' '.join(parsed_address)
            city_name = city_name.translate({ord('{'):None, ord('}'):None, ord('('):None, ord(')'):None, ord('['):None, ord(']'):None})
            # city_name = re.sub('[()]', '', city_name)
            # city_name = re.sub('[[]]', '', city_name)
            # city_name = re.sub('[\{\}]', '', city_name)
            if self.cities_db['Cities'].str.contains(city_name.lower()).any():
                found_city = True
            parsed_address = parsed_address[1:]
            remaining_len += 1
        return city_name, remaining_len
    
    def parse_address(self, address):
        '''
        This function first creates blank placeholders for each field to avoid errors.
        It then parses the address using the usaddress library.
        Because usaddress returns a list of tuples, this function gets the first part of each tuple.
        If the parsed address is too short, we return blanks for each field.
        Otherwise, we start breaking up the address. We always pop our pieces to remove them from the parsed address.
        - First, we get the zip code from the end of the parsed address.
        - Second, we get the state from the end of the parsed address.
        - Third, we get the city from the get_city_name function.
        - Fourth, we parse the rest of the address to get the street number and name.
            - The street number is almost always the first piece of the address.
            - The street name is assumed to be all the pieces with letters that follow the street number.
                - This sometimes results in 'Apt' being included in the street name.
        - Finally, we combine the street number and name into one street address.
        We return the street address, city, state, and zip code.
        '''
        street_address, city, state, zip_code = '', '', '', ''
        
        parsed = usaddress.parse(address)
        
        parsed = [i[0] for i in parsed]
        
        if len(parsed) < 3:
            return street_address, city, state, zip_code
        
        zip_code = parsed.pop(-1)
        state = parsed.pop(-1)
        
        city, remaining_len = self.get_city_name(parsed)
        parsed = parsed[:remaining_len]
        
        street_number = ''
        street_name = ''
        
        while parsed:
            if parsed[0].isnumeric():
                street_number = parsed.pop(0)
            elif any(c.isalpha() for c in parsed[0]):
                street_name = street_name + ' ' + parsed.pop(0)
            else:
                break
        
        if street_number and street_name:
            street_address = street_number.strip() + ' ' + street_name.strip()
        
        return street_address, city, state, zip_code
    
    def get_census_batch(self, addresses):
        '''
        This function sends the input addresses through the address parser and returns them
        in the format the Census geocoder wants.
        '''
        address_column, city_column, state_column, zip_column = [], [], [], []
        for address in addresses:
            street_address, city, state, zip_code = self.parse_address(address)
            address_column.append(street_address)
            city_column.append(city)
            state_column.append(state)
            zip_column.append(zip_code)
        census_batch = pd.DataFrame(list(zip(address_column, city_column, state_column, zip_column)))
        census_batch.to_csv(self.output_filename, header=None)


AddressParser('Downloads/tn_shelby_no_geo.csv', 'Downloads/cities.csv', column_name='address', output_filename='census_batch.csv')
