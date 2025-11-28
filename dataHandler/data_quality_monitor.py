"""
Data Quality Monitoring Module
Detects data quality issues and generates visual reports with candlestick charts
"""

import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging
from dotenv import load_dotenv

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available, charts will be skipped")

load_dotenv()

logger = logging.getLogger(__name__)


class DataQualityMonitor:
    """Monitors data quality and generates reports with visualizations"""
    
    def __init__(self):
        self.base_folder = os.getenv("BASE_FOLDER", "all_ohclv_data")
        self.transf_folder = os.path.join(self.base_folder, "transf_data")
        self.report_dir = Path(os.getenv("QUALITY_REPORT_PATH", "logs/quality_reports"))
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.issues = []
        self.stats = {
            "total_files": 0,
            "total_records": 0,
            "files_with_issues": 0,
            "anomalies_detected": 0
        }
    
    def check_data_quality(self, df, ticker, timeframe):
        """Check data quality for a single ticker/timeframe"""
        issues = []
        
        if df.empty:
            issues.append({"type": "empty_data", "message": "DataFrame is empty"})
            return issues
        
        # Check for missing values
        missing = df[["Open", "High", "Low", "Close", "Volume"]].isna().sum()
        if missing.any():
            issues.append({
                "type": "missing_values",
                "message": f"Missing values: {missing.to_dict()}"
            })
        
        # Check for duplicate timestamps
        date_col = "Date" if "Date" in df.columns else "Datetime"
        duplicates = df[date_col].duplicated().sum()
        if duplicates > 0:
            issues.append({
                "type": "duplicate_timestamps",
                "message": f"Found {duplicates} duplicate timestamps"
            })
        
        # Check price consistency (high >= low, close within range, etc.)
        price_issues = []
        if "High" in df.columns and "Low" in df.columns:
            invalid_high_low = (df["High"] < df["Low"]).sum()
            if invalid_high_low > 0:
                price_issues.append(f"High < Low: {invalid_high_low} rows")
        
        if "Close" in df.columns and "High" in df.columns and "Low" in df.columns:
            close_outside_range = ((df["Close"] > df["High"]) | (df["Close"] < df["Low"])).sum()
            if close_outside_range > 0:
                price_issues.append(f"Close outside High/Low range: {close_outside_range} rows")
        
        if "Open" in df.columns and "High" in df.columns and "Low" in df.columns:
            open_outside_range = ((df["Open"] > df["High"]) | (df["Open"] < df["Low"])).sum()
            if open_outside_range > 0:
                price_issues.append(f"Open outside High/Low range: {open_outside_range} rows")
        
        if price_issues:
            issues.append({
                "type": "price_inconsistency",
                "message": "; ".join(price_issues)
            })
        
        # Check for zero or negative volume
        if "Volume" in df.columns:
            zero_volume = (df["Volume"] <= 0).sum()
            if zero_volume > 0:
                issues.append({
                    "type": "volume_anomaly",
                    "message": f"Zero or negative volume: {zero_volume} rows"
                })
        
        # Check for outliers using Z-score (price changes > 3 standard deviations)
        if "Close" in df.columns and len(df) > 1:
            returns = df["Close"].pct_change().dropna()
            if len(returns) > 0:
                z_scores = np.abs((returns - returns.mean()) / returns.std())
                outliers = (z_scores > 3).sum()
                if outliers > 0:
                    issues.append({
                        "type": "outlier_detection",
                        "message": f"Price outliers (|z| > 3): {outliers} occurrences"
                    })
        
        # Check for gaps in time series
        date_col = "Date" if "Date" in df.columns else "Datetime"
        if date_col in df.columns:
            df_sorted = df.sort_values(date_col)
            if timeframe == "1d":
                # For daily data, check for missing trading days (allow weekends)
                date_diff = df_sorted[date_col].diff()
                # More than 3 days gap might indicate missing data
                large_gaps = (date_diff > pd.Timedelta(days=3)).sum()
                if large_gaps > 0:
                    issues.append({
                        "type": "time_gaps",
                        "message": f"Large time gaps detected: {large_gaps} gaps > 3 days"
                    })
            else:
                # For intraday, check for expected intervals
                date_diff = df_sorted[date_col].diff()
                # This is a simplified check - actual expected interval depends on timeframe
                if len(date_diff) > 1:
                    median_interval = date_diff.median()
                    # Flag if more than 10x median interval
                    large_gaps = (date_diff > median_interval * 10).sum()
                    if large_gaps > 0:
                        issues.append({
                            "type": "time_gaps",
                            "message": f"Large time gaps detected: {large_gaps} gaps"
                        })
        
        return issues
    
    def generate_chart(self, df, ticker, timeframe, issues, output_path):
        """Generate candlestick chart with volume"""
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available, skipping chart generation")
            return
        
        date_col = "Date" if "Date" in df.columns else "Datetime"
        if date_col not in df.columns:
            logger.warning(f"Cannot generate chart for {ticker}_{timeframe}: no date column")
            return
        
        # Prepare data
        df_sorted = df.sort_values(date_col).copy()
        df_sorted = df_sorted.reset_index()
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{ticker} - {timeframe}", "Volume")
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=df_sorted[date_col],
                open=df_sorted["Open"],
                high=df_sorted["High"],
                low=df_sorted["Low"],
                close=df_sorted["Close"],
                name="Price"
            ),
            row=1, col=1
        )
        
        # Volume bars
        fig.add_trace(
            go.Bar(
                x=df_sorted[date_col],
                y=df_sorted["Volume"],
                name="Volume",
                marker_color="blue"
            ),
            row=2, col=1
        )
        
        # Highlight anomalies if any
        if issues:
            issue_text = "<br>".join([f"⚠️ {issue['type']}: {issue['message']}" for issue in issues])
            fig.add_annotation(
                text=issue_text,
                xref="paper", yref="paper",
                x=0.02, y=0.98,
                showarrow=False,
                align="left",
                bgcolor="rgba(255, 200, 200, 0.5)",
                bordercolor="red",
                borderwidth=1
            )
        
        # Update layout
        fig.update_layout(
            title=f"Data Quality Report: {ticker} - {timeframe}",
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        
        # Save chart
        fig.write_html(str(output_path))
        logger.info(f"Generated chart: {output_path}")
    
    def run_checks(self):
        """Run quality checks on all data files"""
        logger.info("Starting data quality checks...")
        
        # Find all CSV files
        csv_files = glob.glob(os.path.join(self.transf_folder, "*.csv"))
        self.stats["total_files"] = len(csv_files)
        
        if not csv_files:
            logger.warning("No CSV files found for quality checks")
            return
        
        report_data = []
        
        for csv_file in csv_files:
            try:
                # Parse ticker and timeframe from filename
                filename = os.path.basename(csv_file).replace(".csv", "")
                parts = filename.split("_")
                ticker = parts[0]
                timeframe = parts[-1]
                
                # Load data
                df = pd.read_csv(csv_file)
                date_col = "Date" if "Date" in df.columns else "Datetime"
                if date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col])
                
                self.stats["total_records"] += len(df)
                
                # Run quality checks
                issues = self.check_data_quality(df, ticker, timeframe)
                
                if issues:
                    self.stats["files_with_issues"] += 1
                    self.stats["anomalies_detected"] += len(issues)
                    self.issues.extend([{**issue, "ticker": ticker, "timeframe": timeframe} for issue in issues])
                
                # Generate chart
                chart_path = self.report_dir / f"{ticker}_{timeframe}_chart.html"
                self.generate_chart(df, ticker, timeframe, issues, chart_path)
                
                report_data.append({
                    "ticker": ticker,
                    "timeframe": timeframe,
                    "records": len(df),
                    "issues": len(issues),
                    "issue_details": issues
                })
                
            except Exception as e:
                logger.error(f"Error processing {csv_file}: {e}", exc_info=True)
                self.issues.append({
                    "type": "processing_error",
                    "ticker": filename,
                    "message": str(e)
                })
        
        # Generate summary report
        self.generate_summary_report(report_data)
        
        logger.info(f"Quality checks completed: {self.stats['files_with_issues']} files with issues out of {self.stats['total_files']} total files")
    
    def generate_summary_report(self, report_data):
        """Generate HTML summary report"""
        report_path = self.report_dir / f"quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .issue {{ color: #d32f2f; font-weight: bold; }}
        .ok {{ color: #388e3c; }}
        .stats {{ background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Data Quality Report</h1>
    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="stats">
        <h2>Summary Statistics</h2>
        <ul>
            <li>Total Files Checked: {self.stats['total_files']}</li>
            <li>Total Records: {self.stats['total_records']:,}</li>
            <li>Files with Issues: {self.stats['files_with_issues']}</li>
            <li>Total Anomalies Detected: {self.stats['anomalies_detected']}</li>
        </ul>
    </div>
    
    <h2>File-by-File Results</h2>
    <table>
        <tr>
            <th>Ticker</th>
            <th>Timeframe</th>
            <th>Records</th>
            <th>Issues</th>
            <th>Status</th>
            <th>Chart</th>
        </tr>
"""
        
        for data in report_data:
            status_class = "issue" if data["issues"] > 0 else "ok"
            status_text = "⚠️ Issues Found" if data["issues"] > 0 else "✓ OK"
            chart_link = f'<a href="{data["ticker"]}_{data["timeframe"]}_chart.html">View Chart</a>' if PLOTLY_AVAILABLE else "N/A"
            
            html_content += f"""
        <tr>
            <td>{data['ticker']}</td>
            <td>{data['timeframe']}</td>
            <td>{data['records']:,}</td>
            <td>{data['issues']}</td>
            <td class="{status_class}">{status_text}</td>
            <td>{chart_link}</td>
        </tr>
"""
        
        html_content += """
    </table>
    
    <h2>Issue Details</h2>
    <table>
        <tr>
            <th>Ticker</th>
            <th>Timeframe</th>
            <th>Issue Type</th>
            <th>Message</th>
        </tr>
"""
        
        for issue in self.issues:
            ticker = issue.get("ticker", "N/A")
            timeframe = issue.get("timeframe", "N/A")
            html_content += f"""
        <tr>
            <td>{ticker}</td>
            <td>{timeframe}</td>
            <td>{issue['type']}</td>
            <td>{issue['message']}</td>
        </tr>
"""
        
        html_content += """
    </table>
</body>
</html>
"""
        
        with open(report_path, "w") as f:
            f.write(html_content)
        
        logger.info(f"Quality report saved: {report_path}")

