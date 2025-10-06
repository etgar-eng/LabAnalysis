import os
import io
from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from functions import Extractor
from main import PdfLabAnalysisReader


def run_processing(lab_name: str, input_pdf_path: str, output_filename: str | None, multi: bool = False) -> str:
    class Args:
        def __init__(self, lab: str, input_path: str, output: str | None, multi_flag: bool):
            self.lab = lab
            self.input = input_path
            self.output = output
            self.multi = 'true' if multi_flag else 'false'

    args = Args(lab_name, input_pdf_path, output_filename, multi)

    extractor_instance = Extractor(args)
    _ = PdfLabAnalysisReader(args)

    df_format = extractor_instance.df_format.copy()
    excel_file = pd.ExcelFile('df_summary.xlsx')
    all_sheets = {}
    output_filename_final = output_filename or lab_name
    output_path = f'{output_filename_final}.xlsx'

    with pd.ExcelWriter(output_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
        for sheet_name in excel_file.sheet_names:
            all_sheets[sheet_name] = excel_file.parse(sheet_name)
            df_format['values'] = df_format['test'].apply(
                lambda i: extractor_instance.search_for_value(all_sheets[sheet_name], i))
            df_format.to_excel(writer, index=False, sheet_name=sheet_name)

    return output_path


def ensure_lab_folder(lab_name: str) -> Path:
    lab_dir = Path.cwd() / lab_name
    lab_dir.mkdir(parents=True, exist_ok=True)
    return lab_dir


def display_summary_statistics(df: pd.DataFrame):
    """Display key statistics from the results"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Tests", len(df))

    with col2:
        detected = df['values'].apply(lambda x: x != 'Not detected' and pd.notna(x)).sum()
        st.metric("Tests Detected", detected)

    with col3:
        not_detected = df['values'].apply(lambda x: x == 'Not detected').sum()
        st.metric("Not Detected", not_detected)


def create_detection_chart(df: pd.DataFrame):
    """Create a pie chart showing detection status"""
    detected = df['values'].apply(lambda x: x != 'Not detected' and pd.notna(x)).sum()
    not_detected = df['values'].apply(lambda x: x == 'Not detected').sum()
    missing = df['values'].isna().sum()

    fig = go.Figure(data=[go.Pie(
        labels=['Detected', 'Not Detected', 'Missing'],
        values=[detected, not_detected, missing],
        hole=.3,
        marker_colors=['#2ecc71', '#e74c3c', '#95a5a6']
    )])

    fig.update_layout(
        title="Detection Status Overview",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig


def create_value_distribution(df: pd.DataFrame):
    """Create histogram of detected values"""
    numeric_df = df[df['values'].apply(lambda x: isinstance(x, (int, float)) and pd.notna(x))].copy()

    if len(numeric_df) > 0:
        fig = px.histogram(
            numeric_df,
            x='values',
            title='Distribution of Detected Values',
            labels={'values': 'Value', 'count': 'Frequency'},
            color_discrete_sequence=['#3498db']
        )
        fig.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        return fig
    return None


def display_formatted_table(df: pd.DataFrame):
    """Display results in a nicely formatted table"""
    display_df = df.copy()

    # Format values for display
    def format_value(x):
        if pd.isna(x) or x == '':
            return 'Missing'
        elif x == 'Not detected':
            return 'Not detected'
        elif isinstance(x, (int, float)):
            return f'{x:.2f}'
        else:
            return str(x)

    display_df['values_formatted'] = display_df['values'].apply(format_value)

    st.dataframe(
        display_df[
            ['test', 'values_formatted', 'units'] if 'units' in display_df.columns else ['test', 'values_formatted']],
        use_container_width=True,
        height=400,
        column_config={
            'test': st.column_config.TextColumn('Test Name', width='large'),
            'values_formatted': st.column_config.TextColumn('Value', width='medium'),
            'units': st.column_config.TextColumn('Units', width='small')
        }
    )


def display_key_findings(df: pd.DataFrame):
    """Highlight key findings and anomalies"""
    # Filter for numeric values and convert to float explicitly
    numeric_mask = df['values'].apply(lambda x: isinstance(x, (int, float)) and pd.notna(x))
    numeric_df = df[numeric_mask].copy()

    # Ensure values column is numeric
    if len(numeric_df) > 0:
        numeric_df['values'] = pd.to_numeric(numeric_df['values'], errors='coerce')
        numeric_df = numeric_df.dropna(subset=['values'])

    col1, col2 = st.columns(2)

    with col1:
        if len(numeric_df) > 0:
            top_5 = numeric_df.nlargest(5, 'values')
            st.write("**Top 5 Highest Values:**")
            for idx, row in top_5.iterrows():
                unit = row.get('units', '')
                st.write(f"- **{row['test']}**: {row['values']:.2f} {unit}")
        else:
            st.info("No numeric values detected")

    with col2:
        not_detected_tests = df[df['values'].astype(str) == 'Not detected']['test'].tolist()
        if not_detected_tests:
            st.write(f"**Tests Not Detected ({len(not_detected_tests)}):**")
            for test in not_detected_tests[:5]:
                st.write(f"- {test}")
            if len(not_detected_tests) > 5:
                st.caption(f"... and {len(not_detected_tests) - 5} more")
        else:
            st.info("All tests detected")


def display_sheet_results(df: pd.DataFrame, sheet_name: str):
    """Display complete analysis for a single sheet"""
    st.subheader(f"Analysis: {sheet_name}")

    # Summary statistics
    display_summary_statistics(df)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        detection_chart = create_detection_chart(df)
        st.plotly_chart(detection_chart, use_container_width=True)

    with col2:
        dist_chart = create_value_distribution(df)
        if dist_chart:
            st.plotly_chart(dist_chart, use_container_width=True)
        else:
            st.info("No numeric values to display distribution")

    # Key findings
    st.subheader("Key Findings")
    display_key_findings(df)

    # Detailed table
    st.subheader("Detailed Results")
    display_formatted_table(df)


def main():
    st.set_page_config(
        page_title="Lab Analysis UI",
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Sidebar
    with st.sidebar:
        st.title("Configuration")
        labs = ['ALS', 'Bactochem', 'Aminolab', 'Element']
        selected_lab = st.selectbox("Select Lab", labs, index=0)
        multi_mode = st.toggle("Multi-labs PDF", value=False,
                               help="Enable if PDF contains multiple labs")
        output_name = st.text_input("Output filename (optional)",
                                    placeholder="Leave empty for default")

        st.divider()
        st.caption("Upload a lab PDF to begin analysis")

    # Main content
    st.title("Lab Analysis Dashboard")
    st.markdown("Upload and analyze laboratory PDF reports with automated data extraction")

    uploaded_pdf = st.file_uploader("Upload Lab PDF", type=["pdf"],
                                    help="Select a PDF file containing lab results")

    if uploaded_pdf is not None:
        st.success(f"File uploaded: **{uploaded_pdf.name}** ({uploaded_pdf.size / 1024:.1f} KB)")

        if st.button("Run Analysis", type="primary", use_container_width=True):
            try:
                lab_dir = ensure_lab_folder(selected_lab)
                temp_pdf_path = lab_dir / uploaded_pdf.name

                with open(temp_pdf_path, 'wb') as f:
                    f.write(uploaded_pdf.getbuffer())

                with st.status("Processing PDF...", expanded=True) as status:
                    st.write("Extracting images and identifying lab...")
                    st.write("Analyzing tables and data...")
                    st.write("Matching values with test parameters...")

                    output_file = run_processing(
                        lab_name=selected_lab,
                        input_pdf_path=str(temp_pdf_path),
                        output_filename=output_name.strip() or None,
                        multi=multi_mode,
                    )

                    status.update(label="Processing Complete!", state="complete")

                st.success(f"Analysis completed! PDF saved to: {temp_pdf_path}")

                # Store results in session state for persistent access
                if 'results_ready' not in st.session_state:
                    st.session_state.results_ready = True
                    st.session_state.output_file = output_file

            except Exception as exc:
                st.error(f"Processing failed: {exc}")
                with st.expander("View error details"):
                    import traceback
                    st.code(traceback.format_exc())

    # Display results section (separate from upload/process button)
    if 'results_ready' in st.session_state and st.session_state.results_ready:
        output_file = st.session_state.output_file

        st.divider()
        st.header("Results")

        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Formatted Results", "Raw Data", "Downloads"])

        with tab1:
            st.subheader("Formatted Results by Sheet")

            if Path(output_file).exists():
                try:
                    final_excel = pd.ExcelFile(output_file)
                    sheet_names = final_excel.sheet_names

                    if len(sheet_names) > 0:
                        # Sheet selector with navigation
                        selected_sheet = st.selectbox(
                            "Select Sheet to View",
                            sheet_names,
                            key="formatted_sheet_selector"
                        )

                        # Load and display the selected sheet
                        final_df = final_excel.parse(selected_sheet)
                        display_sheet_results(final_df, selected_sheet)

                    else:
                        st.warning("No sheets found in the formatted results file")

                except Exception as e:
                    st.error(f"Error loading formatted results: {e}")
                    with st.expander("Error details"):
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.error(f"Formatted results file not found: {output_file}")

        with tab2:
            st.subheader("Raw Extracted Data by Sheet")

            if Path('df_summary.xlsx').exists():
                try:
                    raw_excel = pd.ExcelFile('df_summary.xlsx')
                    sheet_names = raw_excel.sheet_names

                    if len(sheet_names) > 0:
                        # Sheet selector for raw data
                        selected_raw_sheet = st.selectbox(
                            "Select Raw Sheet to View",
                            sheet_names,
                            key="raw_sheet_selector"
                        )

                        # Load and display raw data
                        raw_df = raw_excel.parse(selected_raw_sheet)

                        st.info(f"Sheet: {selected_raw_sheet} | Rows: {len(raw_df)} | Columns: {len(raw_df.columns)}")
                        st.dataframe(raw_df, use_container_width=True, height=500)

                    else:
                        st.warning("No sheets found in raw data file")

                except Exception as e:
                    st.error(f"Error loading raw data: {e}")
                    with st.expander("Error details"):
                        import traceback
                        st.code(traceback.format_exc())
            else:
                st.warning("Raw data file (df_summary.xlsx) not found")

        with tab3:
            st.subheader("Download Results")

            col1, col2 = st.columns(2)

            with col1:
                st.write("**Raw Extracted Data**")
                if Path('df_summary.xlsx').exists():
                    with open('df_summary.xlsx', 'rb') as f:
                        st.download_button(
                            label="Download Raw Data",
                            data=f,
                            file_name='df_summary.xlsx',
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            use_container_width=True,
                        )
                else:
                    st.warning("df_summary.xlsx not available")

            with col2:
                st.write("**Formatted Results**")
                if Path(output_file).exists():
                    with open(output_file, 'rb') as f:
                        st.download_button(
                            label="Download Formatted Results",
                            data=f,
                            file_name=Path(output_file).name,
                            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                            use_container_width=True,
                        )
                else:
                    st.warning(f"{output_file} not available")

    else:
        st.info("Upload a PDF file to begin analysis")


if __name__ == "__main__":
    main()