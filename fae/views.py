from django.shortcuts import render, redirect
from django.http import HttpResponse
import requests
from django.http import JsonResponse
import json
from django.shortcuts import render
from django.http import HttpResponse
import http.cookiejar
import urllib.request
import urllib.parse
import urllib.error
from .models import savedata
from django.conf import settings
import requests
import re



client_id = "8d3dc375-a5e0-478f-a31b-5c92862be79e"
client_secret = "CseSTt5aIZF4SjC9jd72IkpZyJp-zxSqqvwb"
token_url = "https://identity.nexar.com/connect/token"

token = requests.post(url=token_url, data={
    "grant_type": "client_credentials", 
    "client_id": client_id, 
    "client_secret": client_secret,
    "scope": "supply.domain"
}).json()


# views.py

def searh_and_display(request):
    return render(request, "events/search_and_display.html")


def search_all(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')

        # Call the first function (nexar_part_search)
        nexar_results = nexar_part_search(request, search_query)

        # Call the second function (search_mouser)
        mouser_results = search_mouser(request, search_query)

        # You can process the results further or combine them as needed
        combined_results = {
            'nexar_results': nexar_results,
            'mouser_results': mouser_results,
            'search_query': search_query,
        }

        # Render the template with the combined results
        return render(request, 'events/combined.html', combined_results)

    # Return a redirect to the home page for GET requests
    return redirect('home')


def home(request):
    return render(request, 'events/home.html')

def nexar_part_search(request, search_query):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')

        # Replace 'YOUR_NEXAR_ACCESS_TOKEN' with your actual Nexar access token
        access_token = token.get('access_token')

        # Define the GraphQL query
        graphql_query = '''
        query PartSearch($searchQuery: String!) {
          supSearch(
            q: $searchQuery
            filters: {manufacturer_id:["2632", "6645", "87", "196", "7738", "48", "14948", "196", "9332", "519", "6215", "2538", "3900", "4179", "574", "578", "722", "619", "1196", "12041", "14100", "3513", "1139", "14850", "1659", "687", "12043", "11196", "2106", "7517", "665", "2314", "12639", "1482", "3726", "4235", "4057", "13999", "3502", "3930", "7738", "10675", "287", "2060", "1772", "8294", "11948", "621", "3492", "1474", "600", "4900", "10665", "13171", "1479", "360", "13532", "2249", "1333", "3105", "3790", "12397", "8878", "298"]}
            inStockOnly: false
            limit: 10
          ) {
            hits 
            results {
              part {
                similarParts {
                  name
                  octopartUrl
                  mpn
                  }
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
                medianPrice1000 {
                  price
                  currency
                  quantity
                }
                sellers(authorizedOnly: false) {
                  company {
                    name
                    homepageUrl
                  }
                  offers {
                    clickUrl
                    inventoryLevel
                    moq
                    packaging
                  }
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

        # Make the GraphQL request using the requests library
        response = requests.post(nexar_graphql_url, json={'query': graphql_query, 'variables': variables}, headers=headers)

        # Process the response and extract manufacturer information
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('supSearch', {}).get('results', [])

            if results is not None:  # Check if 'results' is not None before iterating
                nexar_results = []

                for result in results:
                    part = result.get('part', {})
                    manufacturer = part.get('manufacturer', {})
                    bestDatasheet = part.get('bestDatasheet', {})

                    result_info = {
                        'mpn': part.get('mpn', ''),
                        'shortDescription': part.get('shortDescription', ''),
                        'manufacturer_name': manufacturer.get('name', ''),
                        'manufacturer_id': manufacturer.get('id', ''),
                        'homepage_url': manufacturer.get('homepageUrl', ''),
                        'is_authorized': False,  # Manufacturers don't have the 'isAuthorized' field
                        # Include other relevant fields
                    }

                    if bestDatasheet:
                        result_info['bestDatasheet_url'] = bestDatasheet.get('url', '')
                    else:
                        result_info['bestDatasheet_url'] = ''

                    nexar_results.append(result_info)

                return nexar_results

    # Return an empty list if no results or for GET requests
    return []

def ms_part_search(request):
    if request.method == 'POST':
        search_query = request.POST.get('search_query', '')

        # Replace 'YOUR_NEXAR_ACCESS_TOKEN' with your actual Nexar access token
        access_token = token.get('access_token')

        # Define the GraphQL query
        graphql_query = '''
        query PartSearch($searchQuery: String!) {
          supSearch(
            q: $searchQuery
            filters: {manufacturer_id: ["2632", "6645", "87", "196", "7738", "48", "14948", "196", "9332", "519", "6215", "2538", "3900", "4179", "574", "578", "722", "619", "1196", "12041", "14100", "3513", "1139", "14850", "1659", "687", "12043", "11196", "2106", "7517", "665", "2314", "12639", "1482", "3726", "4235", "4057", "13999", "3502", "3930", "7738", "10675", "287", "2060", "1772", "8294", "11948", "621", "3492", "1474", "600", "4900", "10665", "13171", "1479", "360", "13532", "2249", "1333", "3105", "3790", "12397", "8878", "298"]}
            inStockOnly: false
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
                medianPrice1000 {
                  price
                  currency
                  quantity
                }
                sellers(authorizedOnly: false) {
                  company {
                    name
                    homepageUrl
                  }
                  offers {
                    clickUrl
                    inventoryLevel
                    moq
                    packaging
                  }
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

        # Make the GraphQL request using the requests library
        response = requests.post(nexar_graphql_url, json={'query': graphql_query, 'variables': variables}, headers=headers)

        # Process the response and extract manufacturer information
        if response.status_code == 200:
            data = response.json()
            results = data.get('data', {}).get('supSearch', {}).get('results', [])

            if results is not None:  # Check if 'results' is not None before iterating
                manufacturers_data = []
                bestDatasheet_data = []

                for result in results:
                    part = result.get('part', {})
                    manufacturer = part.get('manufacturer', {})
                    bestDatasheet = part.get('bestDatasheet', {})
                    
                    if manufacturer:  # Check if the part has a manufacturer
                        offers = part.get('sellers', [])[0].get('offers', [])  # Get offers from the first seller
                        offers_info = []
                        for offer in offers:
                            offer_info = {
                                'click_url': offer.get('clickUrl', ''),
                                'inventory_level': offer.get('inventoryLevel', ''),
                                'moq': offer.get('moq', ''),
                                'packaging': offer.get('packaging', ''),
                            }
                            offers_info.append(offer_info)

                        manufacturer_info = {
                            'manufacturer_name': manufacturer.get('name', ''),
                            'manufacturer_id': manufacturer.get('id', ''),
                            'mpn': part.get('mpn', ''),
                            'shortDescription' : part.get('shortDescription', ''),
                            'homepage_url': manufacturer.get('homepageUrl', ''),
                            'is_authorized': False,  # Manufacturers don't have the 'isAuthorized' field
                            'offers': offers_info,
                        }

                        if bestDatasheet:
                            bestDatasheet_info = {
                                'datasheet_url': bestDatasheet.get('url', ''),
                                }
                        else:
                            bestDatasheet_info = {
                                'datasheet_url': '',
                                }
                            
                    manufacturers_data.append(manufacturer_info)
                    bestDatasheet_data.append(bestDatasheet_info)




                context = {"manufacturers": manufacturers_data,"bestDatasheets": bestDatasheet_data, 'search_query': search_query,}

                # Render the template with the manufacturers' information
                return render(request, 'events/manufacturers_template.html', context)
            else:
                return render(request, 'events/error.html')
        else:
            return render(request, 'events/error_QL.html')

    # Return a redirect to the home page for GET requests
    return redirect('home')

def cheat_sheet(request):
    return render(request, "events/cheatsheet.html", {})

def base_page(request):
    return render(request, "events/base.html")

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
                "records": 25,  # Adjust the number of records as needed
                "startingRecord": 0,
                "searchOptions": "",  # Add search options if needed
                "searchWithYourSignUpLanguage": "",  # Specify language if needed
            }
        }

        # Make the POST request to the Mouser API
        response = requests.post(mouser_api_url, json=request_payload)

        if response.status_code == 200:
            data = response.json()
            parts = data.get('SearchResults', {}).get('Parts', [])

            if parts:  # Check if there are search results
                mouser_results = []

                for part in parts:
                    result_info = {
                        'manufacturer': part.get('Manufacturer', ''),
                        'manufacturerPartNumber': part.get('ManufacturerPartNumber', ''),
                        'description': part.get('Description', ''),
                        'datasheet_url': part.get('DataSheetUrl', ''),
                        # Add other relevant fields
                    }
                    mouser_results.append(result_info)

                return mouser_results

    # Return an empty list if no results or for GET requests
    return []


# def search_mpn(request):
#     if request.method == 'POST':
#         search_query = request.POST.get('search_query', '')

#         # Replace 'YOUR_NEXAR_ACCESS_TOKEN' with your actual Nexar access token
#         access_token = 'YOUR_NEXAR_ACCESS_TOKEN'

#         # Define the GraphQL query for alternative part search
#         graphql_query = '''
#         query findAlternativeParts {
#           supSearchMpn(
#             q: "{search_query}",
#             limit: 5
#           ) {
#             hits
#             results {
#               part {
#                 similarParts {
#                   name
#                   octopartUrl
#                   mpn
#                 }
#               }
#             }
#           }
#         }
#         '''

#         # Set the Nexar GraphQL endpoint
#         nexar_graphql_url = 'https://api.nexar.com/graphql'

#         # Set the authorization header with the access token
#         headers = {
#             'Authorization': f'Bearer {access_token}',
#             'Content-Type': 'application/json',
#         }

#         # Make the GraphQL request using the requests library
#         response = requests.post(nexar_graphql_url, json={'query': graphql_query}, headers=headers)

#         # Process the response and extract alternative part information
#         if response.status_code == 200:
#             data = response.json()
#             results = data.get('data', {}).get('supSearchMpn', {}).get('results', [])

#             if results is not None:
#                 alternative_parts = []

#                 for result in results:
#                     part = result.get('part', {})
#                     similar_parts = part.get('similarParts', [])

#                     for similar_part in similar_parts:
#                         alternative_info = {
#                             'name': similar_part.get('name', ''),
#                             'octopartUrl': similar_part.get('octopartUrl', ''),
#                             'mpn': similar_part.get('mpn', ''),
#                         }

#                         alternative_parts.append(alternative_info)

#                 return render(request, 'nxp_mpn_result.html', {'alternative_parts': alternative_parts})

#     # Return an empty list if no results or for any issues with the request
#     return render(request, 'events/nexar_mpn_result.html', {'alternative_parts': []})


def nexar_alternative_part_search(mpn):
    # Replace 'YOUR_NEXAR_ACCESS_TOKEN' with your actual Nexar access token
    access_token = token.get('access_token')

    # Define the GraphQL query for alternative part search
    manufacturer_ids = ["2632", "6645", "87", "196", "7738", "48", "14948", "196", "9332", "519", "6215", "2538", "3900", "4179", "574", "578", "722", "619", "1196", "12041", "14100", "3513", "1139", "14850", "1659", "687", "12043", "11196", "2106", "7517", "665", "2314", "12639", "1482", "3726", "4235", "4057", "13999", "3502", "3930", "7738", "10675", "287", "2060", "1772", "8294", "11948", "621", "3492", "1474", "600", "4900", "10665", "13171", "1479", "360", "13532", "2249", "1333", "3105", "3790", "12397", "8878", "298"]

    graphql_query = f'''
    query findAlternativeParts {{
      supSearchMpn(
        q: "{mpn}"
        limit: 15) {{
        hits
        results {{
          part {{
            similarParts {{
              name
              octopartUrl
              mpn
              shortDescription
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

    # Make the GraphQL request using the requests library
    response = requests.post(nexar_graphql_url, json={'query': graphql_query}, headers=headers)

    # Process the response and extract alternative part information
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
                    alternative_info = {
                        'name': similar_part.get('name', ''),
                        'shortDescription': similar_part.get('shortDescription', ''),
                        'mpn': similar_part.get('mpn', ''),
                        'bestDatasheet': best_datasheet if best_datasheet else {},
                    }


                    alternative_parts.append(alternative_info)

            return alternative_parts

    # Return an empty list if no results or for any issues with the request
    return []


def search_mpn(request):
    if request.method == 'POST':
        mpn_to_search = request.POST.get('mpn', '')
        alternative_parts_result = nexar_alternative_part_search(mpn_to_search)
        return render(request, 'events/nexar_mpn_result.html', {'alternative_parts': alternative_parts_result})

    return render(request, 'events/nexar_mpn.html')


def mpn(request):
    return render(request, 'events/nexar_mpn.html')