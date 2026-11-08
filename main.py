
import argparse
import os
import sys

import matplotlib
import numpy as np
import pandas as pd

SUBJECTS = ["Math", "Science", "English", "Social_Studies", "Computer_Science"]
PASS_MARK = 40          # minimum marks needed in each subject
MAX_MARKS = 100         # maximum marks per subject
GRADE_BANDS = [         # (lower bound of percentage, grade)
    (90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D"), (40, "E"), (0, "F"),
]
GRADE_ORDER = [g for _, g in GRADE_BANDS]



def load_data(path):
    if not os.path.exists(path):
        sys.exit(f"Error: file '{path}' not found.")
    df = pd.read_csv(path)
    missing = [c for c in SUBJECTS + ["Name"] if c not in df.columns]
    if missing:
        sys.exit(f"Error: missing columns in CSV: {', '.join(missing)}")
    df = df.dropna(subset=SUBJECTS).copy()
    for s in SUBJECTS:
        if not df[s].between(0, MAX_MARKS).all():
            sys.exit(f"Error: '{s}' has marks outside 0-{MAX_MARKS}.")
    return df


def to_grade(pct):
    for bound, grade in GRADE_BANDS:
        if pct >= bound:
            return grade
    return "F"


def calculate(df):
    df["Total"] = df[SUBJECTS].sum(axis=1)
    df["Percentage"] = (df["Total"] / (len(SUBJECTS) * MAX_MARKS) * 100).round(2)
    df["Grade"] = df["Percentage"].apply(to_grade)
    # a student passes only if every subject is at or above the pass mark
    df["Result"] = (df[SUBJECTS] >= PASS_MARK).all(axis=1).map({True: "Pass", False: "Fail"})
    df["Rank"] = df["Total"].rank(ascending=False, method="min").astype(int)
    return df.sort_values("Rank").reset_index(drop=True)


def subject_stats(df):
    rows = []
    for s in SUBJECTS:
        top = df.loc[df[s].idxmax()]
        rows.append({
            "Subject": s,
            "Average": round(df[s].mean(), 2),
            "Highest": df[s].max(),
            "Lowest": df[s].min(),
            "Std_Dev": round(df[s].std(), 2),
            "Pass_Rate_%": round((df[s] >= PASS_MARK).mean() * 100, 1),
            "Topper": top["Name"],
        })
    return pd.DataFrame(rows)


def group_summary(df, column):
    if column not in df.columns:
        return None
    return (df.groupby(column)
              .agg(Students=("Name", "count"),
                   Avg_Percentage=("Percentage", "mean"),
                   Pass_Rate=("Result", lambda r: (r == "Pass").mean() * 100))
              .round(2)
              .reset_index())


def correlations(df):
    cols = [c for c in ["Attendance_Pct", "Study_Hours_Per_Day"] if c in df.columns]
    if not cols:
        return None
    return df[cols + ["Percentage"]].corr().loc[cols, "Percentage"].round(3)


def weakest_subject(row):
    return min(SUBJECTS, key=lambda s: row[s])


def print_overview(df, stats):
    line = "=" * 64
    print(line)
    print("STUDENT RESULT ANALYSER")
    print(line)
    print(f"Students            : {len(df)}")
    print(f"Class average       : {df['Percentage'].mean():.2f}%")
    print(f"Pass percentage     : {(df['Result'] == 'Pass').mean() * 100:.1f}%")
    top = df.iloc[0]
    print(f"Topper              : {top['Name']} ({top['Percentage']}%, grade {top['Grade']})")
    low = df.iloc[-1]
    print(f"Lowest scorer       : {low['Name']} ({low['Percentage']}%)")
    print("\nTop 5 students")
    print(df[["Rank", "Name", "Section", "Total", "Percentage", "Grade"]].head(5).to_string(index=False))
    print("\nSubject statistics")
    print(stats.to_string(index=False))
    for col in ("Section", "Gender"):
        g = group_summary(df, col)
        if g is not None:
            print(f"\n{col}-wise summary")
            print(g.to_string(index=False))
    corr = correlations(df)
    if corr is not None:
        print("\nCorrelation with Percentage")
        print(corr.to_string())
    at_risk = df[(df["Result"] == "Fail") | (df["Percentage"] < 60)]
    if not at_risk.empty:
        print("\nStudents needing attention (fail or below 60%)")
        out = at_risk[["Name", "Percentage", "Result"]].copy()
        out["Weakest_Subject"] = at_risk.apply(weakest_subject, axis=1)
        print(out.to_string(index=False))
    print(line)


def print_report_card(df, name):
    match = df[df["Name"].str.contains(name, case=False, na=False)]
    if match.empty:
        print(f"No student found matching '{name}'.")
        return
    for _, r in match.iterrows():
        print("\n" + "-" * 40)
        print(f"REPORT CARD: {r['Name']}  (Rank {r['Rank']} of {len(df)})")
        print("-" * 40)
        for s in SUBJECTS:
            avg = df[s].mean()
            diff = r[s] - avg
            print(f"{s:<18}{r[s]:>4}   (class avg {avg:.1f}, {diff:+.1f})")
        print(f"{'Total':<18}{r['Total']:>4} / {len(SUBJECTS) * MAX_MARKS}")
        print(f"{'Percentage':<18}{r['Percentage']:>6}%")
        print(f"{'Grade':<18}{r['Grade']:>4}")
        print(f"{'Result':<18}{r['Result']:>6}")
        print(f"Focus area: {weakest_subject(r)}")



def make_charts(df, stats, outdir, show):
    import matplotlib.pyplot as plt
    saved = []

    def finish(fig, filename):
        fig.tight_layout()
        path = os.path.join(outdir, filename)
        fig.savefig(path, dpi=150)
        saved.append(path)
        if not show:
            plt.close(fig)

    # 1. Percentage of every student, coloured by result
    fig, ax = plt.subplots(figsize=(11, 6))
    ordered = df.sort_values("Percentage")
    colors = ["#e74c3c" if r == "Fail" else "#3498db" for r in ordered["Result"]]
    ax.barh(ordered["Name"], ordered["Percentage"], color=colors)
    ax.set_xlabel("Percentage")
    ax.set_title("Student Percentage (red = failed a subject)")
    ax.set_xlim(0, 100)
    finish(fig, "1_student_percentage.png")

    # 2. Subject averages
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(stats["Subject"], stats["Average"], color="#2ecc71")
    ax.bar_label(bars, fmt="%.1f")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Average marks")
    ax.set_title("Subject-wise Class Average")
    finish(fig, "2_subject_average.png")

    # 3. Grade distribution (replaces the original pie of 5 students)
    fig, ax = plt.subplots(figsize=(7, 7))
    counts = df["Grade"].value_counts().reindex(GRADE_ORDER).dropna()
    ax.pie(counts, labels=counts.index, autopct=lambda p: f"{p:.0f}%",
           startangle=90, colors=plt.cm.Set3.colors, wedgeprops={"edgecolor": "white"})
    ax.set_title("Grade Distribution")
    finish(fig, "3_grade_distribution.png")

    # 4. Subject score spread
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot([df[s] for s in SUBJECTS], patch_artist=True)
    ax.set_xticks(range(1, len(SUBJECTS) + 1), SUBJECTS)
    ax.set_ylabel("Marks")
    ax.set_title("Score Spread by Subject")
    finish(fig, "4_subject_spread.png")

    # 5. Heatmap of marks
    fig, ax = plt.subplots(figsize=(8, 8))
    im = ax.imshow(df[SUBJECTS].values, cmap="RdYlGn", vmin=30, vmax=100, aspect="auto")
    ax.set_xticks(range(len(SUBJECTS)), SUBJECTS, rotation=30)
    ax.set_yticks(range(len(df)), df["Name"])
    fig.colorbar(im, ax=ax, label="Marks")
    ax.set_title("Marks Heatmap (ranked top to bottom)")
    finish(fig, "5_marks_heatmap.png")

    # 6. Attendance and study hours vs percentage
    extra = [c for c in ["Attendance_Pct", "Study_Hours_Per_Day"] if c in df.columns]
    if extra:
        fig, axes = plt.subplots(1, len(extra), figsize=(6 * len(extra), 5))
        axes = [axes] if len(extra) == 1 else axes
        for ax, col in zip(axes, extra):
            ax.scatter(df[col], df["Percentage"], color="#9b59b6")
            slope, intercept = np.polyfit(df[col], df["Percentage"], 1)
            xs = df[col].sort_values()
            ax.plot(xs, slope * xs + intercept, color="gray", linestyle="--")
            ax.set_xlabel(col.replace("_", " "))
            ax.set_ylabel("Percentage")
            ax.set_title(f"{col.replace('_', ' ')} vs Percentage")
        finish(fig, "6_attendance_study_vs_percentage.png")

    if show:
        plt.show()
    return saved



def export(df, stats, outdir):
    df.to_csv(os.path.join(outdir, "student_results.csv"), index=False)
    xlsx = os.path.join(outdir, "result_report.xlsx")
    try:
        with pd.ExcelWriter(xlsx) as writer:
            df.to_excel(writer, sheet_name="Results", index=False)
            stats.to_excel(writer, sheet_name="Subjects", index=False)
            for col in ("Section", "Gender"):
                g = group_summary(df, col)
                if g is not None:
                    g.to_excel(writer, sheet_name=f"By_{col}", index=False)
        return [os.path.join(outdir, "student_results.csv"), xlsx]
    except ImportError:
        print("openpyxl not installed, skipped Excel report (pip install openpyxl).")
        return [os.path.join(outdir, "student_results.csv")]



def main():
    parser = argparse.ArgumentParser(description="Student Result Analyser")
    parser.add_argument("--file", default="ENTER PATH TO CSV FILE", help="input CSV")      # ENTER PATH TO CSV FILE
    parser.add_argument("--out", default="output", help="output folder")
    parser.add_argument("--student", help="print report card for a student (name search)")
    parser.add_argument("--show", action="store_true", help="show charts on screen")
    args = parser.parse_args()

    if not args.show:
        matplotlib.use("Agg")

    df = calculate(load_data(args.file))
    stats = subject_stats(df)

    print_overview(df, stats)
    if args.student:
        print_report_card(df, args.student)

    os.makedirs(args.out, exist_ok=True)
    files = export(df, stats, args.out) + make_charts(df, stats, args.out, args.show)
    print(f"\nSaved {len(files)} files to '{args.out}/':")
    for f in files:
        print("  -", os.path.basename(f))


if __name__ == "__main__":
    main()
