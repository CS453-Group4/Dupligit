import csv

# Define the input and output file paths
input_file_path = './msr_paraphrase_dataset/msr_paraphrase_train.txt'  # Adjust the path as needed
output_file_path = 'msr_train.csv'

# Open the input file and the output CSV file
with open(input_file_path, 'r', encoding='utf-8') as infile, open(output_file_path, 'w', newline='', encoding='utf-8') as outfile:
    reader = infile.readlines()
    writer = csv.writer(outfile)
    
    # Write the header row to the CSV
    writer.writerow(['Quality', 'ID1', 'ID2', 'String1', 'String2'])
    
    # Process each line in the input file
    for line in reader:
        # Split the line into components
        parts = line.strip().split('\t')
        if len(parts) == 5:
            quality, id1, id2, string1, string2 = parts
            # Write the data to the CSV
            writer.writerow([quality, id1, id2, string1, string2])

print(f'Dataset has been converted to {output_file_path}')
