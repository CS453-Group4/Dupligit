import csv

SIMILARS_NUM = 20

# Load ground truth
ground_truth = {}
with open('backend/bug_report_dataset/test_thunderbird.csv', newline='') as gt_file:
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
with open('backend/similarity_results.csv', newline='') as tr_file:
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
