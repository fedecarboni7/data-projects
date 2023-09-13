#leer archivos logs.log
import re

results = []
invalid_methods = {'2022': 0, '2023': 0}
franchisees_not_found = {'2022': 0, '2023': 0}
exported_with_errors = {'2022': 0, '2023': 0}
exported_correctly = {'2022': 0, '2023': 0}

with open('main_franchisees_contacts.log') as f:
    lines = f.readlines()
    for line in lines:
        line = line[line.find(' - ')+3:]
        if re.search(r'2022.+fdd\.pdf: invalid methods', line):
            invalid_methods['2022'] += 1
        elif re.search(r'2023.+fdd\.pdf: invalid methods', line):
            invalid_methods['2023'] += 1
        elif re.search(r'2022.+fdd\.pdf: list of franchisees not found', line):
            franchisees_not_found['2022'] += 1
        elif re.search(r'2023.+fdd\.pdf: list of franchisees not found', line):
            franchisees_not_found['2023'] += 1
        elif re.search(r'Exported with errors to: \./test/results_errors/.*-2022.+fdd.csv', line):
            line = line[line.find('Exported with errors to: ./test/results_errors/')+47:-1]
            line += ',Exported with errors\n'
            exported_with_errors['2022'] += 1
        elif re.search(r'Exported with errors to: \./test/results_errors/.*-2023.+fdd.csv', line):
            line = line[line.find('Exported with errors to: ./test/results_errors/')+47:-1]
            line += ',Exported with errors\n'
            exported_with_errors['2023'] += 1
        elif re.search(r'Exported to: \./test/results/.*-2022.+fdd.csv', line):
            line = line[line.find('Exported to: ./test/results/')+28:-1]
            line += ',Exported correctly\n'
            exported_correctly['2022'] += 1
        elif re.search(r'Exported to: \./test/results/.*-2023.+fdd.csv', line):
            line = line[line.find('Exported to: ./test/results/')+28:-1]
            line += ',Exported correctly\n'
            exported_correctly['2023'] += 1
        else: continue
        results.append(line.replace(': ', ',').replace('.', ','))

print('Resultados por año:')
print('2022: ' + 'invalid methods: ' + str(invalid_methods['2022']) + ', franchisees not found: ' + str(franchisees_not_found['2022']) + ', exported with errors: ' + str(exported_with_errors['2022']) + ', exported correctly: ' + str(exported_correctly['2022']))
print('2023: ' + 'invalid methods: ' + str(invalid_methods['2023']) + ', franchisees not found: ' + str(franchisees_not_found['2023']) + ', exported with errors: ' + str(exported_with_errors['2023']) + ', exported correctly: ' + str(exported_correctly['2023']))

# Exportar resultados a archivo txt
with open('results.csv', 'w') as f:
    f.write('fdd_name,extension,output\n')
    results = ''.join(sorted(results))
    f.write(results)
