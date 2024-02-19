from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
from .forms import UploadFileForm
import pandas as pd
from django.db.models import Q
from .models import SelectedPart
from io import BytesIO
from django.db.utils import IntegrityError
from django.contrib import messages
from django.contrib.auth import authenticate, login
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import requests
import json
import os
from django.conf import settings
import csv
BASE_DIR = settings.BASE_DIR

# DIGIKEY INFORMATION
link_for_auth_code="https://sandbox-api.digikey.com/v1/oauth2/authorize?response_type=code&client_id=xl0eqqo8lAy9e8YZeP9bONNKiBGGzTjy&redirect_uri=https://localhost"
dg_client_id="xl0eqqo8lAy9e8YZeP9bONNKiBGGzTjy"
dg_client_secret="bwq4PakC7dQ425T1"
token_filename = 'digikey_token.json'
auth_code="5R566DW9"
token_url = "https://identity.nexar.com/connect/token"
redirect_uri = "https://localhost"
dg_token_filename="fae/dg_token.txt"

#NEXAR INFORMATION
client_id = "588670a8-8ebd-4359-b386-71af4676e701"
client_secret = "HO9-s8TbfNpFDZ9FlySaFzrYCaiH6hd5VZA7"
token = requests.post(url=token_url, data={
    "grant_type": "client_credentials", 
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "supply.domain"
}).json()

def download_sheet(request):
    combined_results = request.session.get("combined_results", {})
    combined_results_filtered = request.session.get("combined_results_filtered", {})
    if 'nexar_results' in combined_results_filtered: 
        results_to_download = combined_results_filtered
        search_query=combined_results_filtered['search_query']
    else:
        search_query=combined_results['search_query']
        results_to_download = combined_results
    print(search_query)
    if not results_to_download:
        return HttpResponse("No data to download.")

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="combined_results.csv"'

    writer = csv.writer(response)
    writer.writerow(['Make', 'MPN', 'Description', 'Datasheet', 'Source', 'Search Query'])

    for key, results in results_to_download.items():
        if key not in ['search_query', 'manufacturer_list', 'mpn_list', 'source_list']:
            for result in results:
                if isinstance(result, dict):
                    make = result.get('make', '')
                    mpn = result.get('mpn', '')
                    description = result.get('description', '')
                    datasheet = result.get('datasheet', '')
                    source = result.get('source', '')
                    writer.writerow([make, mpn, description, datasheet, source, search_query])

    return response

def search_quoted(request, mpn):
    # Initialize variables
    quoted_results = []
    
    # Read data from the Excel sheet
    file_path = "fae\\Book1.xlsx"  # Ensure the correct file path
    df = pd.read_excel(file_path)

    # Input the Customer_part_no you want to search for
    customer_part_no_to_find = mpn

    # Perform the query
    result = df[df['Customer_part_no'] == customer_part_no_to_find]

    # Check if any rows are found
    if not result.empty:
        # Iterate over the rows and extract MS_part_no and M_ Make
        mpn=None
        for index, row in result.iterrows():
            result_context = {
                'source': 'Quoted',
                'mpn': row['MS_part_no'],
                'make': row['M_ Make'],
            }
            if len(result_context['mpn'])>=2:
                quoted_results.append(result_context)
            else:
                print("No mpn")


 
    else:
        print("Customer_part_no not found")

    return quoted_results



def get_refresh_token(token, filename):
    url = 'https://sandbox-api.digikey.com/v1/oauth2/token'

    if not token:
        print("No token provided.")
        return False

    payload = {
        'client_id': dg_client_id,
        'client_secret': dg_client_secret,
        'refresh_token': token['refresh_token'],
        'grant_type': 'refresh_token'
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        response_data = response.json()
        token.update(response_data)  # Update token data with the response
        token['client_id'] = client_id  # Update client_id during token refresh

        with open(filename, "w") as f:
            json.dump(token, f)

        print('\033[32mToken refresh SUCCESS\033[0m')
        file_path = os.path.join(BASE_DIR, 'fae', 'dg_token.txt')
        with open(file_path, 'w') as file:
            file.write(str(token))

        return token

    except requests.exceptions.RequestException as e:
        print('\033[31m\033[1mToken refresh FAILED\033[0m')
        print("Error:", e)
        return False

def load_token_from_file(filename="dg_token.txt"):
    file_path = os.path.join(BASE_DIR, filename)

    # Read the content of the file
    with open(file_path, 'r') as file:
        content = file.read()

    # Extract the dictionary from the content
    token_data = eval(content)
    return token_data


def save_token_to_file(token, filename):
    with open(filename, 'w') as f:
        json.dump(token, f)

def get_access_token(auth_code, filename):
    token = load_token_from_file(filename)
    if token is None:
        token = {}

    url = 'https://sandbox-api.digikey.com/v1/oauth2/token'
    data = {
        'code': auth_code,
        'client_id': dg_client_id,
        'client_secret': dg_client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.post(url, data=data)
        response.raise_for_status()  # Raise an exception for HTTP errors
        response_data = response.json()

        token.update(response_data)  # Update token data with the response
        token['client_id'] = client_id  # Add client_id to the token data

        save_token_to_file(token, filename)  # Save token to file

        print('\033[32mAccess Token get SUCCESS\033[0m')
        return token
    except requests.exceptions.RequestException as e:
        print("Error:", e)
        return None

def get_product_details(partnumber, token):
    partnumber_quoted = partnumber.replace('/', '%2F')
    partnumber_quoted = partnumber_quoted.replace('+', '%2B')
    partnumber_quoted = partnumber_quoted.replace('#', '%23')
    url = f'https://sandbox-api.digikey.com/products/v4/search/{partnumber_quoted}/productdetails'

    print(url)

    url_header = {
        'X-DIGIKEY-Client-Id': "xl0eqqo8lAy9e8YZeP9bONNKiBGGzTjy",
        'x-digikey-locale-Language': 'en',
        'X-DIGIKEY-Locale-Site': 'IN',
        'X-DIGIKEY-Locale-Currency': 'INR',
        'Authorization': f"{token['token_type']} {token['access_token']}",
        'X-DIGIKEY-Customer-Id': '0',
    }

    response = requests.get(url, headers=url_header)

    if response.status_code == 200:
        response_dict = response.json()
        print(f'\033[32mGot information for {partnumber}\033[0m')
        return response_dict
    elif response.status_code == 401:  # Unauthorized, try refreshing token
        print(f'\033[31mUnauthorized. Refreshing token.\033[0m')
        token = get_refresh_token(token, dg_token_filename)
        if token:
            return get_product_details(partnumber, token)
        else:
            print(f'\033[31mFailed to refresh token. Aborting.\033[0m')
            return False
    else:
        print(f'\033[31mFailed to get information for {partnumber}\033[0m')
        print(response.status_code, response.reason)
        return False
    
def search_dg(request, query):
    digikey_results = []

    access_token_data = load_token_from_file(dg_token_filename)

    if access_token_data is None:
        print("Failed to obtain access token.")
        auth_code = input("Enter auth code: \n")
            
        access_token_data = get_access_token(auth_code, token_filename)

    if access_token_data is not None:
        pass
    else:
        print("Failed to obtain or refresh access token.")

    product_details = get_product_details(query, access_token_data)

    if not product_details:
        print("No product found.")
        return digikey_results

    save_token_to_file(access_token_data, token_filename)

    print("Access token obtained successfully.")
    product_variations = product_details['Product']['ProductVariations']
    result_info = {
        'source': 'DigiKey',
        'search_query': query,
        'mpn': product_details['Product']['ManufacturerProductNumber'],
        'description': product_details['Product']['Description']['ProductDescription'],
        'make': product_details['Product']['Manufacturer']['Name'],
        'datasheet': product_details['Product']['DatasheetUrl'],
        'moq': product_variations[0]['MinimumOrderQuantity'],
        'spq': product_variations[0]['StandardPackage'],
    }

    digikey_results.append(result_info)
    alternative_products = product_details.get('SuggestedSubs', [])
    if alternative_products:
        print("\nAlternative Products:")
        for alt_product_details in alternative_products:
            alt_result_info = {
                'search_query': query,
                'mpn': alt_product_details['ManufacturerPartNumber'],
                'description': alt_product_details['ProductDescription'],
                'make': alt_product_details['Manufacturer']['Name'],
                'datasheet': alt_product_details['DatasheetUrl'],
                'moq': alt_product_details['MinimumOrderQuantity'],
                'spq': alt_product_details['StandardPackage'],
            }
            digikey_results.append(alt_result_info)
    else:
        print("\nNo alternative products available.")
    

    return digikey_results


def searh_and_display(request):
    return render(request, "events/search_and_display.html")

def filter(request):
    if request.method == 'POST':
        manufacturers_selected = request.POST.getlist('manufacturers') 
        mpns_selected = request.POST.getlist('mpns')
        sources_selected = request.POST.getlist('sources')

        combined_results = request.session.get("combined_results", {})
        combined_results_filtered = {}

        # Filter by selected manufacturers
        if manufacturers_selected:
            for key, results in combined_results.items():
                if key not in ['search_query', 'manufacturer_list', 'mpn_list', 'source_list']:
                    filtered_results_manufacturer = []
                    for result in results:
                        if isinstance(result, dict) and 'make' in result and result['make'] in manufacturers_selected:
                            filtered_results_manufacturer.append(result)

                    # Apply additional filters if MPNs are selected
                    if mpns_selected:
                        filtered_results_mpn = [r for r in filtered_results_manufacturer if r.get('mpn') in mpns_selected]
                    else:
                        filtered_results_mpn = filtered_results_manufacturer

                    # Apply additional filters if sources are selected
                    if sources_selected:
                        filtered_results_source = [r for r in filtered_results_mpn if r.get('source') in sources_selected]
                        combined_results_filtered[key] = filtered_results_source
                    else:
                        combined_results_filtered[key] = filtered_results_mpn

        # Filter by selected MPNs
        elif mpns_selected:
            for key, results in combined_results.items():
                if key not in ['search_query', 'manufacturer_list', 'mpn_list', 'source_list']:
                    filtered_results_mpn = [r for r in results if isinstance(r, dict) and 'mpn' in r and r['mpn'] in mpns_selected]

                    if sources_selected:
                        filtered_results_source = [r for r in filtered_results_mpn if r.get('source') in sources_selected]
                        combined_results_filtered[key] = filtered_results_source
                    else:
                        combined_results_filtered[key] = filtered_results_mpn

        elif sources_selected:
            for key, results in combined_results.items():
                if key not in ['search_query', 'manufacturer_list', 'mpn_list', 'source_list']:
                    filtered_results_source = [r for r in results if isinstance(r, dict) and 'source' in r and r['source'] in sources_selected]
                    combined_results_filtered[key] = filtered_results_source


        combined_results_filtered['mpn_list']=combined_results['mpn_list']
        combined_results_filtered['source_list']=combined_results['source_list']
        combined_results_filtered["manufacturer_list"]=combined_results['manufacturer_list']
        combined_results_filtered["search_query"]=combined_results['search_query']
        request.session['combined_results_filtered']=combined_results_filtered
        if 'reset' in request.POST:
            return render(request, 'events/combined.html', combined_results)
        return render(request, 'events/combined.html', combined_results_filtered)

    return redirect('home')
  
def search_all(request):
    if request.method == 'POST':

        search_query = request.POST.get('search_query', '')

        nexar_results = nexar_part_search(request, search_query)

        irc_results = search_irc(request, search_query)

        nexar_alt_results = search_nexar_alt(request, search_query)

        mouser_result = search_mouser(request, search_query)

        digikey_results=search_dg(request,search_query)

        quoted=search_quoted(request,search_query)
        request.session["quoted"]=quoted
        manufacturer_list=[]
        mpn_list=[]
        source_list=[]
        
        combined_results = {
            'nexar_results': nexar_results,
            'irc_results': irc_results,
            'nexar_alt_results': nexar_alt_results,
            'mouser_results': mouser_result,
            'search_query': search_query,
            'digikey_results': digikey_results,  
            'quoted':quoted,
        }

        for key, results in combined_results.items():
            if key != 'search_query' and key != 'manufacturer_list':
                for result in results:
                    if isinstance(result, dict):
                        if result['make'] not in manufacturer_list:
                            manufacturer_list.append(result['make'])
                        if result['mpn'] not in mpn_list:
                            mpn_list.append(result['mpn'])
                        if result['source'] not in source_list:
                            source_list.append(result['source'])

        combined_results['mpn_list']=mpn_list
        combined_results['source_list']=source_list
        combined_results["manufacturer_list"]=manufacturer_list
        request.session["combined_results"] = combined_results
        return render(request, 'events/combined.html', combined_results)

    return redirect('home')

def nexar_part_search(request, search_query):
    access_token = token.get('access_token')

    graphql_query = '''
    query PartSearch($searchQuery: String!) {
      supSearch(
        q: $searchQuery
        limit: 10
      ) {
        hits 
        results {
          part {
            mpn
            shortDescription
            manufacturer {
              name
              id
              homepageUrl
            }
            bestDatasheet {
               url
            }
          }
        }
      }
    }
    '''


    # Set the Nexar GraphQL endpoint
    nexar_graphql_url = 'https://api.nexar.com/graphql'

    # Set the authorization header with the access token
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    # Define the query variables
    variables = {'searchQuery': search_query}

    try:
        # Make the GraphQL request using the requests library
        response = requests.post(nexar_graphql_url, json={'query': graphql_query, 'variables': variables}, headers=headers)
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('supSearch', {}).get('results', [])

            if results:
                nexar_results = []

                for result in results:
                    part = result.get('part', {})
                    manufacturer = part.get('manufacturer', {})
                    best_datasheet = part.get('bestDatasheet', {})
                    result_info = {
                        'search_query': search_query,
                        'source': 'Nexar',
                        'mpn': part.get('mpn', ''),
                        'description': part.get('shortDescription', ''),
                        'make': manufacturer.get('name', ''),
                        'homepage_url': manufacturer.get('homepageUrl', ''),
                        'datasheet': best_datasheet if best_datasheet else {},
                    }
                    
                    if best_datasheet:
                        result_info['datasheet'] = best_datasheet.get('url', '')
                    else:
                        result_info['datasheet'] = ''
                    nexar_results.append(result_info)
                return nexar_results
            else:
                print("No results found from Nexar API.")
        else:
            print(f"Nexar API request failed with status code: {response.status_code}")

    except Exception as e:
        print(f"Error occurred while fetching data from Nexar API: {str(e)}")

    return []  # Return an empty list if no results or if an error occurred


def cheat_sheet(request):
    return render(request, "events/cheatsheet.html", {})

def base_page(request):
    parts_count = SelectedPart.objects.count()
    return render(request, "events/base.html", {'parts_count': parts_count})

def search_mouser(request, search_query):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')

        # Replace 'YOUR_MOUSER_API_KEY' with your actual Mouser API key
        api_key = '69967069-746f-48a9-9d9c-9cb1c423c9b6'

        # Define the Mouser API URL with the provided query parameters
        mouser_api_url = f'https://api.mouser.com/api/v2/search/keyword?apiKey={api_key}'

        # Construct the request payload using the provided query format
        request_payload = {
            "SearchByKeywordRequest": {
                "keyword": search_query,
                "records": 50,
                "startingRecord": 0,
                "searchOptions": "",  # Add search options if needed
                "searchWithYourSignUpLanguage": "",  # Specify language if needed
            }
        }

        # Make the POST request to the Mouser API
        response = requests.post(mouser_api_url, json=request_payload)
        if response.status_code == 200:
            data = response.json()
            if data is not None:
                parts = data.get('SearchResults', {}).get('Parts', [])
            else:
                parts = []


            mouser_results = []

            for part in parts:
                result_info = {
                    'source': 'Mouser',
                    'make': part.get('Manufacturer', ''),
                    'mpn': part.get('ManufacturerPartNumber', ''),
                    'description': part.get('Description', ''),
                    'datasheet': part.get('DataSheetUrl', ''),
                    'moq': part.get('Min', ''),
                    'spq': None
                }
                # Get the Standard Pack Quantity if available
                product_attributes = part.get('ProductAttributes', [])
                for attribute in product_attributes:
                    if attribute.get('AttributeName') == 'Standard Pack Qty':
                        result_info['spq'] = attribute.get('AttributeValue')
                        break

                mouser_results.append(result_info)

            return mouser_results


    # Return an empty list if no results or for GET requests
    return []
def search_nexar_alt(request, search_query):
    print("here")
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        
        # Replace 'YOUR_NEXAR_ACCESS_TOKEN' with your actual Nexar access token
        access_token = token.get('access_token')

        # Define the GraphQL query for alternative part search
        manufacturer_ids = ["2632", "6645", "87", "196", "7738", "48", "14948", "196", "9332", "519", "6215", "2538", "3900", "4179", "574", "578", "722", "619", "1196", "12041", "14100", "3513", "1139", "14850", "1659", "687", "12043", "11196", "2106", "7517", "665", "2314", "12639", "1482", "3726", "4235", "4057", "13999", "3502", "3930", "7738", "10675", "287", "2060", "1772", "8294", "11948", "621", "3492", "1474", "600", "4900", "10665", "13171", "1479", "360", "13532", "2249", "1333", "3105", "3790", "12397", "8878", "298"]

        graphql_query = f'''
        query findAlternativeParts {{
          supSearchMpn(
            q: "{search_query}"
            limit: 15) 
            {{
            hits
            results {{
              part {{
                similarParts {{
                  name
                  octopartUrl
                  mpn
                  shortDescription
                  manufacturer {{
                    name
                    id
                    homepageUrl
                }}
                  bestDatasheet {{
                    pageCount
                    createdAt
                    url
                  }}
                }}
              }}
            }}
          }}
        }}
        '''

        # Set the Nexar GraphQL endpoint
        nexar_graphql_url = 'https://api.nexar.com/graphql'

        # Set the authorization header with the access token
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        variables = {'searchQuery': search_query}
        # Make the GraphQL request using the requests library
        response = requests.post(nexar_graphql_url, json={'query': graphql_query, 'variables': variables}, headers=headers)

        # Process the response and extract alternative part information
        print("threre")
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('supSearchMpn', {}).get('results', [])

            if results is not None:
                alternative_parts = []
                for result in results:
                    part = result.get('part', {})
                    similar_parts = part.get('similarParts', [])

                    for similar_part in similar_parts:
                        best_datasheet = similar_part.get('bestDatasheet', {})
                        manufacturer = similar_part.get('manufacturer', {})
                        alternative_info = {
                            'source': 'Nexar alt.',
                            'description': similar_part.get('shortDescription', ''),
                            'mpn': similar_part.get('mpn', ''),
                            'datasheet': best_datasheet if best_datasheet else {},
                            'search_query': search_query,
                            'make': manufacturer.get('name', ''),
                            'homepage_url': manufacturer.get('homepageUrl', ''),
                            'manufacturer_id': manufacturer.get('id', ''),
                        }
                        print('there')
                        if best_datasheet:
                            alternative_info['datasheet'] = best_datasheet.get('url', '')
                        else:
                            alternative_info['datasheet'] = ''
                        alternative_parts.append(alternative_info)
            return alternative_parts

    # Return an empty list if no results or for any issues with the request
    return []




def store_selected_parts(request):
    if request.method == 'POST':
        selected_parts = request.POST.getlist('selectedParts[]')

        for part in selected_parts:
            mpn, name, short_description, datasheet_url, search_query = (part.split('|') + [None, None, None, None, None])[:5]

            try:
                # Attempt to create a new record
                selected_part, created = SelectedPart.objects.get_or_create(
                    mpn=mpn,
                    defaults={
                        'name': name,
                        'description': short_description,
                        'datasheet': datasheet_url,
                        'search_query': search_query,
                    }
                )

                if not created and search_query:  # Check if the record already existed and search_query is not None
                    # Assign to Equivalent fields based on matching search query
                    for i in range(1, 6):  # Assuming Equivalent_1 to Equivalent_5
                        equivalent_field_name = f'Equivalent_{i}'
                        if not getattr(selected_part, equivalent_field_name):
                            setattr(selected_part, equivalent_field_name, part)
                            selected_part.save()
                            break  # Stop after assigning to the first available Equivalent field

            except IntegrityError:
                # Handle exceptions (e.g., IntegrityError) based on your requirements
                print("Error storing part:", part)

        return HttpResponse('Selected parts have been successfully stored.')

    return HttpResponse('Invalid request method.')

def upload_checked_parts(request):
    if request.method == 'POST':
        selected_parts = request.POST.getlist('selectedParts[]')

        for part in selected_parts:
            mpn, manufacturer, description, datasheet_url, search_query = (part.split('|') + [None, None, None, None, None])[:5]

            try:
                SelectedPart.objects.create(
                    mpn=mpn,
                    make=manufacturer,
                    description=description,
                    datasheet=datasheet_url,
                    search_query=search_query,
                )

            except IntegrityError as e:
                # Handle IntegrityError (e.g., log the error)
                print(f"Error uploading part: {part}. Error: {e}")

        return HttpResponse('Selected parts have been successfully stored.')

    return HttpResponse('Invalid request method.')

def export_to_excel(request):
    # Get all objects from the model
    queryset = SelectedPart.objects.all()

    # Convert queryset to a DataFrame
    df = pd.DataFrame.from_records(queryset.values())

    # Create an in-memory Excel file
    excel_file = BytesIO()
    df.to_excel(excel_file, index=False, engine='openpyxl')

    # Set response headers for the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=Data.xlsx'

    # Write the Excel file to the response
    excel_file.seek(0)
    response.write(excel_file.getvalue())

    return response

def search_dynamic(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')
        search_option = request.POST.get('search_option', '')

        if search_option == 'description':
            return search_all(request, search_query) 
        elif search_option == 'mpn':
            return search_nexar_alt(request, search_query)  
        elif search_option == 'irc':
            return search_irc(request, search_query) 

def import_data(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Read the Excel file into a DataFrame
            excel_file = request.FILES['file']
            if excel_file.name.endswith('.xlsx'):
                df = pd.read_excel(excel_file, engine='openpyxl')
            elif excel_file.name.endswith('.xls'):
                df = pd.read_excel(excel_file, engine='xlrd')
            else:
                return render(request, 'error.html', {'error_message': 'Unsupported file format'})

            # Define the required column names
            required_columns = ['make', 'mpn', 'description', 'datasheet', 'search_query']

            # Process the DataFrame and save data to the database
            for index, row in df.iterrows():
                # Match the required columns dynamically
                row_dict = {col: row[col] for col in row.index if col.lower() in required_columns}

                # Check if all required columns exist in the DataFrame
                if all(col in row_dict for col in required_columns):
                    # Check if a record with the same MPN already exists
                    existing_record = SelectedPart.objects.filter(mpn=row_dict['mpn']).first()
                    
                    if existing_record:
                        # Update the existing record or handle as needed
                        existing_record.make = row_dict['make']
                        existing_record.description = row_dict['description']
                        existing_record.datasheet = row_dict['datasheet']
                        existing_record.search_query = row_dict['search_query']
                        existing_record.save()
                    else:
                        # Create a new record
                        SelectedPart.objects.create(
                            mpn=row_dict['mpn'],
                            make=row_dict['make'],
                            description=row_dict['description'],
                            datasheet=row_dict['datasheet'],
                            search_query=row_dict['search_query'],
                            # Add other fields as needed
                        )

            # Display a success message on the same page
            messages.success(request, 'Data imported successfully!')

            # Reload the form to clear any previous data
            form = UploadFileForm()

    else:
        form = UploadFileForm()

    return render(request, 'events/import_data.html', {'form': form})


def download_template(request):
    # Create a simple DataFrame as a template
    data = {'make': [], 'mpn': [], 'description': [], 'datasheet': [], 'search_query': []}  # Define the required columns
    df_template = pd.DataFrame(data)

    # Save the DataFrame to an Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=template.xlsx'
    df_template.to_excel(response, index=False, engine='openpyxl')

    return response


def search_irc(request, search_query):
    irc_results = []
    irc_result = SelectedPart.objects.filter(
        Q(mpn__icontains=search_query) |
        Q(name__icontains=search_query) |
        Q(short_description__icontains=search_query) |
        Q(datasheet_url__icontains=search_query) |
        Q(search_query__icontains=search_query) |
        Q(Equivalent_1__icontains=search_query) |
        Q(Equivalent_2__icontains=search_query) |
        Q(Equivalent_3__icontains=search_query) |
        Q(Equivalent_4__icontains=search_query) |
        Q(Equivalent_5__icontains=search_query)
    )
    for part in irc_result:
        context = {
            'mpn':part.mpn,
            'source': 'IRC',
            'make': part.name,
            'search_query': search_query,
            'description': part.short_description,
            'datasheet': part.datasheet_url,
        }
        # Append context to irc_results inside the loop
        irc_results.append(context)
    
    # Return irc_results after the loop
    return irc_results

def export_page(request):
    return render(request, 'events/export.html')

def admin_page(request):
    return render(request, 'events/admin.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return render(request, 'events/data.html') # Assuming 'data_page' is the name of the URL pattern for data.html
        else:
            messages.error(request, 'Invalid username or password.')
    
def getting_started(request):
    return render(request, 'events/getting_started.html')
