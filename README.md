# Student Result Analyser

A Python project that turns a CSV of student marks into a complete result analysis: totals, percentages, grades, pass/fail, ranks, subject statistics, section and gender comparisons, charts and an Excel report.

## Features
- Total, percentage, grade (A+ to F), Pass/Fail and rank for every student
- Pass rule: at least 40 marks in every subject
- Subject statistics: average, highest, lowest, standard deviation, pass rate, topper
- Section-wise and gender-wise summaries
- Correlation of attendance and study hours with performance
- List of students needing attention, with their weakest subject
- Individual report card with comparison to the class average
- 6 charts saved as PNG, plus `student_results.csv` and `result_report.xlsx`

## Setup
```
pip install -r requirements.txt
```

## Usage
```
python analyser.py
python analyser.py --student "Priya"
python analyser.py --file my_marks.csv --out results --show
```

## CSV format
Required columns: `Name`, `Math`, `Science`, `English`, `Social_Studies`, `Computer_Science`.
Optional columns used when present: `Student_ID`, `Gender`, `Section`, `Attendance_Pct`, `Study_Hours_Per_Day`.

To change subjects, pass mark or grade bands, edit the constants at the top of `analyser.py`.

## Output
All files are written to the `output/` folder (or the folder given by `--out`).
