import csv
import os

SIMILARS_NUM = 20

# Load ground truth
ground_truth = {}

script_dir = os.path.dirname(os.path.realpath(__file__))

test_file_path = os.path.join(script_dir, 'bug_report_dataset/test_thunderbird.csv')
with open(test_file_path, newline='') as gt_file:
    reader = csv.DictReader(gt_file)
    for row in reader:
        issue_id = row['Issue_id']
        duplicates = row['Duplicate']
        if duplicates == 'NULL':
            ground_truth[issue_id] = set()
        else:
            ground_truth[issue_id] = set(duplicates.split(';'))

# Load test results
test_results = {}
result_file_path = os.path.join(script_dir, 'similarity_results_miniLM.csv')

with open(result_file_path, newline='') as tr_file:
    reader = csv.DictReader(tr_file)
    for row in reader:
        issue_id = row['Issue_id']
        top_predictions = []
        for i in range(1, SIMILARS_NUM + 1):
            sim_id = row[f'Similar_issue_id_{i}']
            top_predictions.append(sim_id)
        test_results[issue_id] = set(top_predictions)

# Evaluate true positives and false negatives
true_positive = 0
false_negative = 0
total_issues = 0

for issue_id, predicted_duplicates in test_results.items():
    true_duplicates = ground_truth.get(issue_id, set())
    if true_duplicates:
        total_issues += 1
        if predicted_duplicates & true_duplicates:
            true_positive += 1
        else:
            false_negative += 1

# Calculate metrics
recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0

# Print summary
print(f"\nSummary:")
print(f"Total Issues with Duplicates: {total_issues}")
print(f"True Positives:               {true_positive}")
print(f"False Negatives:              {false_negative}")
print(f"Recall:                       {recall:.2%}")

true_positive_examples = []
no_duplicate_ground_truth = []

for issue_id, predicted_duplicates in test_results.items():
    true_duplicates = ground_truth.get(issue_id, set())

    if not true_duplicates and len(no_duplicate_ground_truth) < 15:
        no_duplicate_ground_truth.append(issue_id)

    elif true_duplicates:
        if predicted_duplicates & true_duplicates and len(true_positive_examples) < 15:
            true_positive_examples.append((issue_id, true_duplicates, predicted_duplicates))

    if (len(true_positive_examples) >= 15 and
        len(no_duplicate_ground_truth) >= 15):
        break

# Write to CSV
examples_file_path = os.path.join(script_dir, 'evaluation_examples.csv')

with open(examples_file_path, 'w', newline='') as csvfile:
    fieldnames = ['Case_Type', 'Issue_ID', 'Ground_Truth_Duplicates', 'Predicted_Duplicates']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    for issue_id, gt, pred in true_positive_examples:
        writer.writerow({
            'Case_Type': 'True Positive',
            'Issue_ID': issue_id,
            'Ground_Truth_Duplicates': ';'.join(gt),
            'Predicted_Duplicates': ';'.join(pred)
        })

    for issue_id in no_duplicate_ground_truth:
        writer.writerow({
            'Case_Type': 'No Duplicate in Ground Truth',
            'Issue_ID': issue_id,
            'Ground_Truth_Duplicates': '',
            'Predicted_Duplicates': ';'.join(test_results[issue_id])
        })
