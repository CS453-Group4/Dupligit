import csv
import os
import sys
from typing import List, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.gemini_validation import validate_similarity_with_gemini_test_dataset

script_dir = os.path.dirname(os.path.realpath(__file__))

issue_bodies = {}

data_path = os.path.join(script_dir, 'bug_report_dataset', 'bug_reports_thunderbird.csv')
with open(data_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        issue_id = row["Issue_id"]
        issue_bodies[issue_id] = (row["Title"] + " " + row["Description"]).strip()

# Process evaluation examples
results = []
examples_path = os.path.join(script_dir, 'evaluation_examples.csv')
with open(examples_path, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        issue_id = row["Issue_ID"]
        ground_truth = row["Ground_Truth_Duplicates"].split(';') if row["Ground_Truth_Duplicates"] else []
        predicted = row["Predicted_Duplicates"].split(';') if row["Predicted_Duplicates"] else []

        # Build the similar_issues list
        similar_issues = []
        for pid in predicted:
            similar_issues.append({
                "id": int(pid),
                "body": issue_bodies.get(pid, ""),
                "ground_truth": ground_truth  # Add GT for evaluation
            })

        issue_body = issue_bodies.get(issue_id, "")
        gemini_results = validate_similarity_with_gemini_test_dataset(issue_body, similar_issues)

        # Warn about invalid indexes
        for res in gemini_results:
            if not (0 <= res["matched_issue_index"] < len(similar_issues)):
                print(f"⚠️ Invalid index {res['matched_issue_index']} for issue {issue_id}")

        # Handle only valid indexes
        matched_ids = {
            str(similar_issues[res["matched_issue_index"]]["id"])
            for res in gemini_results
            if res["verdict"] == "Correct" and 0 <= res["matched_issue_index"] < len(similar_issues)
        }

        matched_str = ";".join(sorted(matched_ids))
        truth_str = ";".join(sorted(ground_truth))

        case_type = "True Positive" if ground_truth and matched_ids.intersection(ground_truth) else (
            "False Negative" if ground_truth else "No Duplicate in Ground Truth"
        )

        results.append({
            "Case_Type": case_type,
            "Issue_ID": issue_id,
            "Ground_Truth_Duplicates": truth_str,
            "Predicted_Duplicates": matched_str
        })

# Write to CSV
with open('gemini_evaluation_results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["Case_Type", "Issue_ID", "Ground_Truth_Duplicates", "Predicted_Duplicates"])
    writer.writeheader()
    writer.writerows(results)

print("✅ Results written to gemini_evaluation_results.csv")
