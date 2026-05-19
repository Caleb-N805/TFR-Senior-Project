from pathlib import Path
import re
import pandas as pd


def _parse_metadata_from_filename(filename):
    """
    Expected filename pattern like:
    misctest-W4-H12-SB.csv

    Returns:
    wafer='W4', die='H12', resistor_type='SB'
    """
    stem = Path(filename).stem
    tokens = re.split(r"[-_\s]+", stem)

    wafer = die = resistor_type = None

    for i, token in enumerate(tokens):
        if wafer is None and re.fullmatch(r"W\d+", token, flags=re.IGNORECASE):
            wafer = token.upper()
            continue

        if wafer is not None and die is None:
            if re.fullmatch(r"[A-Z]+\d+", token, flags=re.IGNORECASE):
                die = token.upper()

                if i + 1 < len(tokens):
                    resistor_type = tokens[i + 1].upper()

                break

    if wafer is None or die is None or resistor_type is None:
        raise ValueError(
            f"Could not parse wafer/die/resistor type from filename: {filename}"
        )

    return wafer, die, resistor_type


def _get_numeric_series_by_label(raw, label):
    """
    Finds a label such as 't' or 'R' anywhere in the sheet.
    Then extracts the numeric series either below it or to its right,
    whichever has more numeric values.
    """
    label_lower = label.lower()

    best_series = None
    best_count = -1

    for row_idx in range(raw.shape[0]):
        for col_idx in range(raw.shape[1]):
            cell = str(raw.iat[row_idx, col_idx]).strip().lower()

            if cell != label_lower:
                continue

            below = pd.to_numeric(
                raw.iloc[row_idx + 1 :, col_idx], errors="coerce"
            ).reset_index(drop=True)

            right = pd.to_numeric(
                raw.iloc[row_idx, col_idx + 1 :], errors="coerce"
            ).reset_index(drop=True)

            candidates = [below, right]

            for candidate in candidates:
                count = candidate.notna().sum()
                if count > best_count:
                    best_count = count
                    best_series = candidate

    if best_series is None or best_count == 0:
        raise ValueError(f"Could not find numeric data for label '{label}'")

    return best_series


def summarize_resistance_sheet(sheet, failure_percent, metadata_source=None):
    """
    Returns 7 values:
    1. Wafer number
    2. Die number
    3. Resistor type
    4. Initial resistance
    5. Minimum resistance
    6. Time to minimum resistance
    7. Time to failure

    failure_percent:
        Pass 5 for 5%, 10 for 10%, etc.

    sheet:
        CSV filepath or pandas DataFrame.

    metadata_source:
        Optional filename/string to parse wafer, die, and resistor type from.
        Useful if passing a DataFrame instead of a filepath.
    """
    if failure_percent < 0:
        raise ValueError("failure_percent must be non-negative")

    if isinstance(sheet, (str, Path)):
        path = Path(sheet)
        raw = pd.read_csv(path, header=None, dtype=str)
        metadata_source = metadata_source or path.name

    elif isinstance(sheet, pd.DataFrame):
        # Include column headers as a row, so labels like 't' and 'R'
        # are still detectable if the DataFrame was read normally.
        header_row = pd.DataFrame([list(sheet.columns)])
        raw = pd.concat(
            [header_row, sheet.reset_index(drop=True)],
            ignore_index=True
        ).astype(str)

        if metadata_source is None:
            raise ValueError(
                "metadata_source is required when passing a DataFrame, "
                "unless you modify the function to pass wafer/die/type directly."
            )

    else:
        raise TypeError("sheet must be a CSV filepath or a pandas DataFrame")

    wafer, die, resistor_type = _parse_metadata_from_filename(metadata_source)

    t = _get_numeric_series_by_label(raw, "t")
    r = _get_numeric_series_by_label(raw, "R")

    # Align valid t/R pairs
    valid = t.notna() & r.notna()
    t = t[valid].reset_index(drop=True)
    r = r[valid].reset_index(drop=True)

    if len(r) == 0:
        raise ValueError("No valid paired t/R data found")

    initial_resistance = float(r.iloc[0])

    min_idx = int(r.idxmin())
    minimum_resistance = float(r.iloc[min_idx])
    time_to_minimum = float(t.iloc[min_idx])

    failure_threshold = minimum_resistance * (1 + failure_percent / 100)

    # Search only after the minimum occurs
    failure_time = float(t.iloc[-1])
    for i in range(min_idx, len(r)):
        if r.iloc[i] >= failure_threshold:
            failure_time = float(t.iloc[i])
            break

    device_lifetime = failure_time - time_to_minimum

    return (
        wafer,
        die,
        resistor_type,
        initial_resistance,
        minimum_resistance,
        time_to_minimum,
        failure_time,
        device_lifetime
    )

#log_path = r"C:\Users\cnomi\Documents\GitHub\TFR-Senior-Project\misc_testing_logs\misctest-W4-C6-SA.csv"

#wafer, die, resistor_type, r_chuck, r_min, t_min, t_fail, t_device_lifetime = summarize_resistance_sheet(log_path, 10)


def summarize_folder(input_folder, output_csv, failure_percent, pattern="*.csv"):
    input_folder = Path(input_folder)

    results = []
    errors = []

    for csv_file in input_folder.glob(pattern):
        try:
            (
                wafer,
                die,
                resistor_type,
                initial_resistance,
                minimum_resistance,
                time_to_minimum,
                time_to_failure,
                device_lifetime
            ) = summarize_resistance_sheet(
                csv_file,
                failure_percent=failure_percent
            )

            results.append({
                "Wafer": wafer,
                "Die": die,
                "Resistor Type": resistor_type,
                "Initial Resistance": initial_resistance,
                "Minimum Resistance": minimum_resistance,
                "Time to Minimum Resistance": time_to_minimum,
                "Time to Failure": time_to_failure,
                "Device Lifetime": device_lifetime,
            })

        except Exception as e:
            errors.append({
                "Source File": csv_file.name,
                "Error": str(e),
            })

    results_df = pd.DataFrame(results)
    results_df.to_csv(output_csv, index=False)

    if errors:
        error_csv = Path(output_csv).with_name(
            Path(output_csv).stem + "_errors.csv"
        )
        pd.DataFrame(errors).to_csv(error_csv, index=False)
        print(f"Finished with {len(errors)} errors. See: {error_csv}")

    print(f"Saved {len(results)} results to: {output_csv}")

    return results_df

summarize_folder(
    input_folder=r"C:\Users\cnomi\Documents\GitHub\TFR-Senior-Project\misc_testing_logs",
    output_csv="new_misc_results2.csv",
    failure_percent=10
)