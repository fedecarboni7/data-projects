def regex():
    regex_list = [r'(\d+,\d+|\d+)\s*(?:[a-z]+|\–|\-)\s*(\d+,\d+|\d+)\s*(?:square|sq\.)\s*(?:f..t|ft\.)',
                  r'(\d+,\d+|\d+)\s*(?:square|sq\.)\s*(?:f..t|ft\.)']
    return regex_list
    