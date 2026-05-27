"""
app.py – Streamlit Lab Analysis Dashboard  (v2.1)
"""

from __future__ import annotations

import io
import re
import traceback
from pathlib import Path

import pandas as pd
import streamlit as st

from functions import Extractor
from main import PdfLabAnalysisReader
from report import ReportBuilder, ReportMeta

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

LAB_CHOICES = ["ALS", "Bactochem", "Aminolab", "Element"]

_SHEET = "דוח רשות המים"

_C_PARAM  = "פרמטר (רשות המים)"
_C_LNAME  = "פרמטר (מעבדה)"
_C_RVAL   = "תוצאה (מקורית)"
_C_RUNIT  = "יחידה (מקורית)"
_C_WVAL   = 'תוצאה (רש"מ)'
_C_WUNIT  = 'יחידות (רש"מ)'
_C_LIMIT  = "גבול תקנות 2013"
_C_STATUS = "סטטוס"
_C_IS_SEC = "_is_section"   # internal marker column, never displayed

_ALL_COLS  = [_C_PARAM, _C_LNAME, _C_RVAL, _C_RUNIT, _C_WVAL, _C_WUNIT, _C_LIMIT, _C_STATUS]
_VIEW_COLS = [_C_PARAM, _C_WVAL, _C_WUNIT, _C_LIMIT, _C_STATUS]

_STATUS_CELL: dict[str, str] = {
    "תקין":           "background-color:#C6EFCE;color:#276221;font-weight:bold",
    "חריג!":          "background-color:#FF6B6B;color:#7B0000;font-weight:bold",
    "בגבול גילוי":   "background-color:#FFD700;color:#7D6608;font-weight:bold",
    "לא ניתן לאמת":  "background-color:#FFD700;color:#7D6608;font-weight:bold",
    "לא נבדק":        "background-color:#F2F2F2;color:#888888",
}
_ROW_BG: dict[str, str] = {
    "תקין":           "background-color:#EAF7EA",
    "חריג!":          "background-color:#FFDEDE",
    "בגבול גילוי":   "background-color:#FFFDE7",
    "לא ניתן לאמת":  "background-color:#FFFDE7",
    "לא נבדק":        "",
}
_SECTION_STYLE = (
    "background-color:#2E75B6;color:#FFFFFF;"
    "font-weight:bold;font-style:italic"
)


# ─────────────────────────────────────────────────────────────────────────────
# Processing
# ─────────────────────────────────────────────────────────────────────────────

def _run_processing(
    lab_name: str,
    pdf_path: str,
    site: str = "",
    multi: bool = False,
) -> tuple[list[tuple[str, Path]], dict[str, pd.DataFrame]]:
    """Extract tables from PDF, build per-check *_report.xlsx files.

    Returns:
        report_files : list of (check_name, report_path)
        sheet_data   : raw extracted DataFrames keyed by check_name
    """

    class _Args:
        def __init__(self_):   # noqa: N805
            self_.lab    = lab_name
            self_.input  = pdf_path
            self_.output = None
            self_.multi  = "true" if multi else "false"
            self_.site   = site
            self_.date   = ""
            self_.time   = ""

    args      = _Args()
    extractor = Extractor(args)
    reader    = PdfLabAnalysisReader(args)

    report_files: list[tuple[str, Path]] = []
    for sheet_name, df_raw in reader.sheet_data.items():
        meta = ReportMeta(
            report_number=Path(pdf_path).stem,
            site=sheet_name if sheet_name else site,
            sampling_date=reader.sample_dates.get(sheet_name, ""),
            lab_name=lab_name,
        )
        builder = ReportBuilder(
            df_raw=df_raw,
            df_format=extractor.df_format,
            params=extractor.params,
            meta=meta,
        )
        safe = re.sub(r"[\\/*?:\[\]\s]", "_", sheet_name)
        out  = Path(f"{safe}_report.xlsx")
        builder.build(out)
        report_files.append((sheet_name, out))

    return report_files, dict(reader.sheet_data)


# ─────────────────────────────────────────────────────────────────────────────
# Report reading  (faithfully mirrors the Excel layout)
# ─────────────────────────────────────────────────────────────────────────────

def _load_report(path: Path) -> tuple[pd.DataFrame, dict]:
    """Parse *_report.xlsx  →  (df_data, meta_dict).

    • Keeps ALL non-empty rows including section-header rows.
    • Section headers are marked with _C_IS_SEC == True.
    • meta_dict keys: 'site', 'date', 'lab'
    """
    # ── Metadata (first 6 rows, no header) ────────────────────────────────
    raw_top = pd.read_excel(
        path, sheet_name=_SHEET, header=None, nrows=6, engine="openpyxl"
    )

    def _v(r: int, c: int) -> str:
        try:
            v = raw_top.iat[r, c]
            return str(v).strip() if pd.notna(v) else ""
        except Exception:
            return ""

    meta = {"site": _v(1, 2), "date": _v(2, 2), "lab": _v(3, 2)}

    # ── Data table – read without pre-assigned header first ───────────────
    # Use header=None so we can find the real header row robustly
    raw_all = pd.read_excel(
        path, sheet_name=_SHEET, header=None, engine="openpyxl"
    )

    # Find the header row (contains "סטטוס" in any cell)
    header_row_idx = None
    for idx in range(min(15, len(raw_all))):
        vals = raw_all.iloc[idx].astype(str).tolist()
        if _C_STATUS in vals or _C_PARAM in vals:
            header_row_idx = idx
            break

    if header_row_idx is None:
        return pd.DataFrame(), meta

    # Build DataFrame from rows below the header
    headers = raw_all.iloc[header_row_idx].tolist()
    df      = raw_all.iloc[header_row_idx + 1:].copy()
    df.columns = headers
    df = df.reset_index(drop=True)

    # Keep only the expected named columns
    df = df[[c for c in _ALL_COLS if c in df.columns]]

    # Remove completely blank rows
    df = df.dropna(how="all").reset_index(drop=True)

    # Mark section-header rows: they have text in _C_PARAM but NaN in _C_STATUS
    if _C_STATUS in df.columns:
        df[_C_IS_SEC] = df[_C_STATUS].isna() & df[_C_PARAM].notna()
    else:
        df[_C_IS_SEC] = False

    return df, meta


# ─────────────────────────────────────────────────────────────────────────────
# Pandas Styler helpers
# ─────────────────────────────────────────────────────────────────────────────

def _style_check_row(row: pd.Series) -> list[str]:
    """Row-level style: blue for section headers, colour-coded for data rows."""
    if row.get(_C_IS_SEC, False):
        return [_SECTION_STYLE] * len(row.index)
    status = str(row.get(_C_STATUS, ""))
    bg     = _ROW_BG.get(status, "")
    cell   = _STATUS_CELL.get(status, "")
    return [cell if col == _C_STATUS else bg for col in row.index]


def _style_summary_row(row: pd.Series) -> list[str]:
    styles: list[str] = []
    for col in row.index:
        if col.startswith("סטטוס – "):
            s = str(row[col]) if pd.notna(row[col]) else "לא נבדק"
            styles.append(_STATUS_CELL.get(s, ""))
        elif col.startswith("תוצאה – "):
            check    = col[len("תוצאה – "):]
            stat_val = row.get(f"סטטוס – {check}")
            s        = str(stat_val) if pd.notna(stat_val) else "לא נבדק"
            styles.append(_ROW_BG.get(s, ""))
        elif col == _C_LIMIT:
            styles.append("font-weight:bold;background-color:#EBF5FB")
        elif col == _C_PARAM:
            styles.append("font-weight:bold")
        else:
            styles.append("")
    return styles


# ─────────────────────────────────────────────────────────────────────────────
# Per-check tab renderer
# ─────────────────────────────────────────────────────────────────────────────

def _render_check(
    check_name: str,
    report_path: Path,
    df_raw: pd.DataFrame | None = None,
) -> None:
    """Render one check's results inside its Streamlit tab.

    Mirrors the Excel layout exactly: section headers shown as blue rows,
    all parameters shown (including 'לא נבדק').
    """
    if not report_path.exists():
        st.error(f"דוח לא נמצא: `{report_path}`")
        return

    try:
        df, meta = _load_report(report_path)
    except Exception as exc:
        st.error(f"שגיאה בקריאת {report_path.name}: {exc}")
        with st.expander("פרטי שגיאה"):
            st.code(traceback.format_exc())
        return

    if df.empty:
        st.warning("לא נמצאו שורות נתונים בדוח.")
        return

    # ── Metadata ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.metric("📍 אתר דיגום",  meta["site"] or check_name)
    c2.metric("📅 מועד דיגום", meta["date"] or "—")
    c3.metric("🔬 מעבדה",      meta["lab"]  or "—")

    # ── Status KPIs ───────────────────────────────────────────────────────
    st.divider()
    data_rows = df[~df[_C_IS_SEC]] if _C_IS_SEC in df.columns else df
    counts = (
        data_rows[_C_STATUS].value_counts()
        if _C_STATUS in data_rows.columns
        else pd.Series(dtype=int)
    )
    tested = sum(
        int(counts.get(s, 0))
        for s in ("תקין", "חריג!", "בגבול גילוי", "לא ניתן לאמת")
    )
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🔬 נבדקו",        tested)
    k2.metric("✅ תקין",          int(counts.get("תקין",          0)))
    k3.metric("🔴 חריג!",         int(counts.get("חריג!",         0)))
    k4.metric("⚠️ בגבול גילוי",  int(counts.get("בגבול גילוי",   0)))
    k5.metric("⬜ לא נבדק",       int(counts.get("לא נבדק",       0)))

    # ── Filters (apply only to data rows, not section headers) ───────────
    st.divider()
    fa, fb = st.columns([1, 2])
    all_statuses = (
        sorted(data_rows[_C_STATUS].dropna().unique().tolist())
        if _C_STATUS in data_rows.columns else []
    )
    sel_status  = fa.multiselect(
        "סנן לפי סטטוס", all_statuses,
        default=[], key=f"sf_{check_name}",
    )
    search_text = fb.text_input(
        "🔍 חפש פרמטר", key=f"st_{check_name}",
        placeholder="הקלד שם פרמטר...",
    )

    # Build filtered view: always keep section headers
    if sel_status or search_text.strip():
        is_sec  = df[_C_IS_SEC] if _C_IS_SEC in df.columns else pd.Series(False, index=df.index)
        mask    = is_sec.copy()  # start with "keep all section headers"
        d_mask  = ~is_sec
        if sel_status:
            d_mask = d_mask & df[_C_STATUS].isin(sel_status)
        if search_text.strip():
            d_mask = d_mask & df[_C_PARAM].astype(str).str.contains(
                search_text.strip(), case=False, na=False
            )
        df_view = df[mask | d_mask].copy()
    else:
        df_view = df.copy()

    n_data = int((~df_view[_C_IS_SEC]).sum()) if _C_IS_SEC in df_view.columns else len(df_view)
    st.caption(f"מציג **{n_data}** פרמטרים")

    # ── Main results table (5 focused columns + section headers) ─────────
    view_cols  = [c for c in _VIEW_COLS if c in df_view.columns] + [_C_IS_SEC]
    df_display = df_view[[c for c in view_cols if c in df_view.columns]].copy()

    styled = df_display.style.apply(_style_check_row, axis=1)
    # Hide the internal _is_section column from display
    if _C_IS_SEC in df_display.columns:
        styled = styled.hide(axis="columns", subset=[_C_IS_SEC])

    st.dataframe(styled, use_container_width=True, height=560, hide_index=True)

    # ── Full-detail expander (8 columns) ──────────────────────────────────
    with st.expander("🔬 נתוני מעבדה מקוריים – כל העמודות"):
        full_disp = df_view[[c for c in _ALL_COLS + [_C_IS_SEC] if c in df_view.columns]].copy()
        sf = full_disp.style.apply(_style_check_row, axis=1)
        if _C_IS_SEC in full_disp.columns:
            sf = sf.hide(axis="columns", subset=[_C_IS_SEC])
        st.dataframe(sf, use_container_width=True, height=420, hide_index=True)

    # ── Raw extraction debug ──────────────────────────────────────────────
    if df_raw is not None and not df_raw.empty:
        with st.expander("🔍 ניפוי שגיאות – נתוני מיצוי גולמיים (df_raw)"):
            unit_counts = df_raw["units"].value_counts().to_dict() \
                if "units" in df_raw.columns else {}
            st.info(
                f"**{len(df_raw)}** שורות מוצאו  —  "
                + "  |  ".join(f"{u}: {n}" for u, n in unit_counts.items())
            )
            st.dataframe(df_raw, use_container_width=True, height=350, hide_index=True)

    # ── Download ──────────────────────────────────────────────────────────
    with open(report_path, "rb") as fh:
        st.download_button(
            label=f"⬇️ הורד דוח Excel – {report_path.name}",
            data=fh.read(),
            file_name=report_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key=f"dl_{check_name}",
        )


# ─────────────────────────────────────────────────────────────────────────────
# Summary tab renderer
# ─────────────────────────────────────────────────────────────────────────────

def _render_summary(report_files: list[tuple[str, Path]]) -> None:
    """Side-by-side comparison: all checks × all parameters + Israeli standard (last col)."""
    st.subheader("📊 סיכום השוואתי – כל הבדיקות מול תקן ישראלי")

    check_dfs: list[tuple[str, pd.DataFrame]] = []
    for name, path in report_files:
        if not path.exists():
            continue
        try:
            df, _ = _load_report(path)
            # Only data rows (not section headers) for the summary
            if _C_IS_SEC in df.columns:
                df = df[~df[_C_IS_SEC]].drop(columns=[_C_IS_SEC], errors="ignore")
            check_dfs.append((name, df))
        except Exception:
            continue

    if not check_dfs:
        st.warning("אין נתונים להצגה.")
        return

    # ── Build merged table (value + status per check) ─────────────────────
    merged: pd.DataFrame | None = None
    for check_name, df in check_dfs:
        if _C_PARAM not in df.columns or _C_WVAL not in df.columns:
            continue
        keep = [_C_PARAM, _C_WUNIT, _C_WVAL, _C_STATUS]
        sub  = df[[c for c in keep if c in df.columns]].copy()
        sub  = sub.rename(columns={
            _C_WVAL:   f"תוצאה – {check_name}",
            _C_STATUS: f"סטטוס – {check_name}",
        })
        if merged is None:
            merged = sub
        else:
            new_cols = [f"תוצאה – {check_name}", f"סטטוס – {check_name}"]
            new_cols = [c for c in new_cols if c in sub.columns]
            merged = merged.merge(sub[[_C_PARAM] + new_cols], on=_C_PARAM, how="outer")

    if merged is None or merged.empty:
        st.warning("לא ניתן לבנות טבלת סיכום.")
        return

    # ── Collect limits (same for all checks; take first non-null per param) ─
    limit_rows: list[pd.DataFrame] = []
    for _, df in check_dfs:
        if _C_PARAM in df.columns and _C_LIMIT in df.columns:
            limit_rows.append(df[[_C_PARAM, _C_LIMIT]].dropna(subset=[_C_LIMIT]))
    if limit_rows:
        limit_df = (
            pd.concat(limit_rows)
            .drop_duplicates(_C_PARAM)
            .reset_index(drop=True)
        )
        merged = merged.merge(limit_df, on=_C_PARAM, how="left")

    # ── Re-order: param | unit | (val|status)×N | standard ───────────────
    val_cols    = [c for c in merged.columns if c.startswith("תוצאה – ")]
    status_cols = [c for c in merged.columns if c.startswith("סטטוס – ")]
    interleaved = [c for pair in zip(val_cols, status_cols) for c in pair]
    unit_col    = [_C_WUNIT] if _C_WUNIT in merged.columns else []
    limit_col   = [_C_LIMIT] if _C_LIMIT in merged.columns else []
    merged = merged[[_C_PARAM] + unit_col + interleaved + limit_col].reset_index(drop=True)

    # ── Filters ───────────────────────────────────────────────────────────
    f1, f2 = st.columns(2)
    show_nd    = f1.toggle("הצג 'לא נבדק'",          value=False, key="sum_nd")
    only_issue = f2.toggle("חריגות ואזהרות בלבד",     value=False, key="sum_issue")

    display = merged.copy()
    s_cols  = [c for c in status_cols if c in display.columns]

    if not show_nd and s_cols:
        mask = display[s_cols].apply(
            lambda col: col.fillna("לא נבדק").ne("לא נבדק")
        ).any(axis=1)
        display = display[mask]

    if only_issue and s_cols:
        mask = display[s_cols].apply(
            lambda col: col.isin(["חריג!", "בגבול גילוי", "לא ניתן לאמת"])
        ).any(axis=1)
        display = display[mask]

    st.caption(
        f"**{len(display)}** פרמטרים  |  **{len(val_cols)}** בדיקות  "
        f"|  עמודה אחרונה = תקן ישראלי (תקנות בריאות העם 2013)"
    )

    styled = display.style.apply(_style_summary_row, axis=1)
    st.dataframe(styled, use_container_width=True, height=600, hide_index=True)

    buf = io.BytesIO()
    display.to_excel(buf, index=False)
    buf.seek(0)
    st.download_button(
        label="⬇️ הורד טבלת סיכום Excel",
        data=buf.read(),
        file_name="summary_all_checks.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key="dl_summary",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_lab_dir(lab_name: str) -> Path:
    d = Path.cwd() / lab_name
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# Main Streamlit app
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Lab Analysis Dashboard",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown(
        """<style>
        [data-testid="metric-container"] {
            background:#F8F9FA; border-radius:8px; padding:6px 10px;
        }
        </style>""",
        unsafe_allow_html=True,
    )

    # ── Sidebar ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("🧪 Lab Analyzer")
        st.divider()
        lab   = st.selectbox("🏭 בחר מעבדה", LAB_CHOICES)
        site  = st.text_input("📍 שם אתר הדיגום", placeholder="קידוח 5 / ביג פתח תקוה...")
        multi = st.toggle("🔀 PDF מרובה מעבדות", value=False)
        st.divider()
        st.caption("Water Authority Lab Analyzer · v2.1")

    # ── Page header ───────────────────────────────────────────────────────
    st.title("🧪 Lab Analysis Dashboard")
    st.markdown("העלה PDF של דוח מעבדה לניתוח אוטומטי ויצוא לפורמט **רשות המים**.")

    # ── PDF uploader ──────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📂 העלה קובץ PDF של דוח מעבדה", type=["pdf", "PDF"]
    )

    if uploaded is None:
        st.info("⬆️ העלה קובץ PDF ובחר מעבדה מהתפריט הצדדי כדי להתחיל.")
        return

    col_info, col_btn = st.columns([3, 1])
    col_info.success(
        f"✅ **{uploaded.name}**  ·  {uploaded.size / 1024:.1f} KB  ·  מעבדה: **{lab}**"
    )

    if col_btn.button("▶️ הפעל ניתוח", type="primary", use_container_width=True):
        try:
            lab_dir  = _ensure_lab_dir(lab)
            pdf_path = lab_dir / uploaded.name
            with open(pdf_path, "wb") as f:
                f.write(uploaded.getbuffer())

            with st.status("⚙️ מעבד...", expanded=True) as status_box:
                st.write(f"📄 קורא טבלאות מ-**{uploaded.name}**…")
                st.write("📊 בונה דוחות Excel…")
                report_files, sheet_data = _run_processing(
                    lab_name=lab,
                    pdf_path=str(pdf_path),
                    site=site.strip(),
                    multi=multi,
                )
                # Show extraction summary inside the status
                for sname, sdf in sheet_data.items():
                    unit_cnt = sdf["units"].value_counts().to_dict() \
                        if "units" in sdf.columns else {}
                    summary  = "  |  ".join(f"{u}: {n}" for u, n in unit_cnt.items())
                    st.write(f"  ✔ **{sname}**: {len(sdf)} שורות — {summary}")

                status_box.update(
                    label=f"✅ הסתיים! נמצאו **{len(report_files)}** בדיקות.",
                    state="complete",
                )

            st.session_state["report_files"]  = report_files
            st.session_state["sheet_data"]    = sheet_data
            st.session_state["results_ready"] = True

        except Exception as exc:
            st.error(f"❌ שגיאה: {exc}")
            with st.expander("פרטי שגיאה"):
                st.code(traceback.format_exc())
            return

    # ── Results ───────────────────────────────────────────────────────────
    if not st.session_state.get("results_ready"):
        return

    report_files: list[tuple[str, Path]] = st.session_state["report_files"]
    sheet_data:   dict[str, pd.DataFrame] = st.session_state.get("sheet_data", {})

    if not report_files:
        st.warning("לא נמצאו בדיקות בדוח.")
        return

    st.divider()
    st.header(f"📊 תוצאות — {len(report_files)} בדיקות")

    # Tabs: one per check + Summary last
    tab_labels = [f"🔬 {name}" for name, _ in report_files] + ["📊 סיכום"]
    tabs = st.tabs(tab_labels)

    for tab, (check_name, report_path) in zip(tabs[:-1], report_files):
        with tab:
            df_raw = sheet_data.get(check_name)
            _render_check(check_name, report_path, df_raw=df_raw)

    with tabs[-1]:
        _render_summary(report_files)


if __name__ == "__main__":
    main()
