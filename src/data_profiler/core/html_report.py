"""HTML report generation with interactive visualizations."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import plotly.graph_objects as go
import plotly.express as px
from jinja2 import Template
import pandas as pd

from data_profiler.models.profile import DataProfile, ColumnProfile
from data_profiler.core.drift_detection import DatasetDrift


class HTMLReportGenerator:
    """Generate interactive HTML reports with visualizations."""

    @staticmethod
    def generate_profile_report(
        profile: DataProfile,
        output_path: Optional[str] = None,
        title: str = "Data Profile Report",
    ) -> str:
        """
        Generate comprehensive HTML report for a data profile.

        Args:
            profile: DataProfile to generate report for
            output_path: Optional path to save HTML file
            title: Report title

        Returns:
            HTML content as string
        """
        # Generate visualizations
        overview_section = HTMLReportGenerator._create_overview_section(profile)
        quality_section = HTMLReportGenerator._create_quality_section(profile)
        column_sections = HTMLReportGenerator._create_column_sections(profile)
        correlation_section = HTMLReportGenerator._create_correlation_section(profile)
        recommendations_section = HTMLReportGenerator._create_recommendations_section(profile)

        # Combine sections
        html_content = HTMLReportGenerator._render_template(
            title=title,
            overview=overview_section,
            quality=quality_section,
            columns=column_sections,
            correlation=correlation_section,
            recommendations=recommendations_section,
            profile=profile,
        )

        # Save to file if path provided
        if output_path:
            Path(output_path).write_text(html_content)

        return html_content

    @staticmethod
    def generate_drift_report(
        drift: DatasetDrift,
        baseline_profile: DataProfile,
        current_profile: DataProfile,
        output_path: Optional[str] = None,
        title: str = "Drift Analysis Report",
    ) -> str:
        """
        Generate drift comparison HTML report.

        Args:
            drift: DatasetDrift comparison results
            baseline_profile: Baseline profile
            current_profile: Current profile
            output_path: Optional path to save HTML file
            title: Report title

        Returns:
            HTML content as string
        """
        # Generate drift visualizations
        drift_overview = HTMLReportGenerator._create_drift_overview(drift)
        drift_details = HTMLReportGenerator._create_drift_details(drift)
        drift_charts = HTMLReportGenerator._create_drift_charts(
            drift, baseline_profile, current_profile
        )

        # Combine sections
        html_content = HTMLReportGenerator._render_drift_template(
            title=title,
            drift_overview=drift_overview,
            drift_details=drift_details,
            drift_charts=drift_charts,
            drift=drift,
        )

        # Save to file if path provided
        if output_path:
            Path(output_path).write_text(html_content)

        return html_content

    @staticmethod
    def _create_overview_section(profile: DataProfile) -> str:
        """Create overview section with key metrics."""
        fig = go.Figure()

        # Create metrics cards
        metrics = {
            "Total Rows": profile.row_count,
            "Total Columns": profile.column_count,
            "Memory Usage (MB)": round(profile.memory_bytes / 1024 / 1024, 2),
            "Profile Time (s)": round(profile.profiling_duration_seconds, 3),
        }

        # Create a simple bar chart for metrics
        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(metrics.keys()),
                    y=list(metrics.values()),
                    marker_color="lightblue",
                    text=list(metrics.values()),
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Profile Overview",
            showlegend=False,
            height=400,
            template="plotly_white",
        )

        return fig.to_html(include_plotlyjs="cdn", div_id="overview")

    @staticmethod
    def _create_quality_section(profile: DataProfile) -> str:
        """Create data quality visualization."""
        # Calculate overall quality metrics
        completeness_scores = []
        uniqueness_scores = []
        column_names = []

        for col in profile.columns:
            column_names.append(col.name)
            completeness_scores.append(col.quality.completeness)
            uniqueness_scores.append(col.quality.uniqueness)

        # Create quality heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=[completeness_scores, uniqueness_scores],
                x=column_names,
                y=["Completeness (%)", "Uniqueness (%)"],
                colorscale="RdYlGn",
                text=[[f"{v:.1f}" for v in completeness_scores], [f"{v:.1f}" for v in uniqueness_scores]],
                texttemplate="%{text}",
                textfont={"size": 10},
                colorbar=dict(title="Score (%)"),
            )
        )

        fig.update_layout(
            title="Data Quality Metrics by Column",
            height=300,
            template="plotly_white",
        )

        return fig.to_html(include_plotlyjs=False, div_id="quality")

    @staticmethod
    def _create_column_sections(profile: DataProfile) -> List[str]:
        """Create visualization sections for each column."""
        sections = []

        for col in profile.columns:
            section_html = f"<h3>{col.name} <span class='badge'>{col.type.value}</span></h3>"

            # Numeric column visualization
            if col.numeric_stats:
                fig = HTMLReportGenerator._create_numeric_visualization(col)
                section_html += fig.to_html(include_plotlyjs=False, div_id=f"col_{col.name}")

            # Categorical column visualization
            elif col.categorical_stats:
                fig = HTMLReportGenerator._create_categorical_visualization(col)
                section_html += fig.to_html(include_plotlyjs=False, div_id=f"col_{col.name}")

            # Add quality metrics
            section_html += f"""
            <div class='stats-grid'>
                <div class='stat-card'>
                    <div class='stat-label'>Completeness</div>
                    <div class='stat-value'>{col.quality.completeness:.1f}%</div>
                </div>
                <div class='stat-card'>
                    <div class='stat-label'>Uniqueness</div>
                    <div class='stat-value'>{col.quality.uniqueness:.1f}%</div>
                </div>
                <div class='stat-card'>
                    <div class='stat-label'>Null Count</div>
                    <div class='stat-value'>{col.quality.null_count:,}</div>
                </div>
            </div>
            """

            sections.append(section_html)

        return sections

    @staticmethod
    def _create_numeric_visualization(col: ColumnProfile) -> go.Figure:
        """Create visualization for numeric column."""
        stats = col.numeric_stats

        if not stats:
            return go.Figure()

        # Create box plot
        fig = go.Figure()

        # Add box plot
        fig.add_trace(
            go.Box(
                y=[stats.min, stats.q25, stats.median, stats.q75, stats.max],
                name="Distribution",
                boxmean="sd",
            )
        )

        # Add annotations for key stats
        annotations_text = f"Mean: {stats.mean:.2f}<br>Std: {stats.std:.2f}"
        if stats.outlier_count and stats.outlier_count > 0:
            annotations_text += f"<br>Outliers: {stats.outlier_count}"

        fig.add_annotation(
            text=annotations_text,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
        )

        fig.update_layout(
            title=f"{col.name} - Distribution",
            height=400,
            showlegend=False,
            template="plotly_white",
        )

        return fig

    @staticmethod
    def _create_categorical_visualization(col: ColumnProfile) -> go.Figure:
        """Create visualization for categorical column."""
        stats = col.categorical_stats

        if not stats or not stats.top_values:
            return go.Figure()

        # Create bar chart for top values
        values = list(stats.top_values.keys())[:10]  # Top 10
        counts = list(stats.top_values.values())[:10]

        fig = go.Figure(
            data=[
                go.Bar(
                    x=values,
                    y=counts,
                    marker_color="lightcoral",
                    text=counts,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title=f"{col.name} - Top Values (Total: {stats.unique_count} unique)",
            xaxis_title="Value",
            yaxis_title="Count",
            height=400,
            template="plotly_white",
        )

        return fig

    @staticmethod
    def _create_correlation_section(profile: DataProfile) -> str:
        """Create correlation heatmap."""
        if not profile.correlation_matrix:
            return "<p>No correlation data available</p>"

        # Convert correlation matrix to DataFrame
        df = pd.DataFrame(profile.correlation_matrix)

        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=df.values,
                x=df.columns,
                y=df.index,
                colorscale="RdBu",
                zmid=0,
                text=df.values,
                texttemplate="%{text:.2f}",
                textfont={"size": 10},
                colorbar=dict(title="Correlation"),
            )
        )

        fig.update_layout(
            title="Correlation Matrix",
            height=600,
            template="plotly_white",
        )

        return fig.to_html(include_plotlyjs=False, div_id="correlation")

    @staticmethod
    def _create_recommendations_section(profile: DataProfile) -> str:
        """Create recommendations section."""
        if not profile.recommendations:
            return "<p>No recommendations available</p>"

        html = "<div class='recommendations'>"

        # Group by severity
        severity_icons = {
            "critical": "🔴",
            "warning": "🟡",
            "info": "ℹ️",
        }

        severity_colors = {
            "critical": "#ff4444",
            "warning": "#ffaa00",
            "info": "#4444ff",
        }

        for rec in profile.recommendations:
            icon = severity_icons.get(rec.severity, "ℹ️")
            color = severity_colors.get(rec.severity, "#4444ff")

            html += f"""
            <div class='recommendation' style='border-left: 4px solid {color}'>
                <div class='rec-header'>
                    <span class='rec-icon'>{icon}</span>
                    <span class='rec-severity' style='color: {color}'>{rec.severity.upper()}</span>
                    <span class='rec-title'>{rec.title}</span>
                </div>
                <div class='rec-description'>{rec.description}</div>
                {f"<div class='rec-suggestion'>💡 {rec.suggestion}</div>" if rec.suggestion else ""}
            </div>
            """

        html += "</div>"
        return html

    @staticmethod
    def _create_drift_overview(drift: DatasetDrift) -> str:
        """Create drift overview visualization."""
        # Create gauge chart for overall drift score
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=drift.overall_drift_score * 100,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Overall Drift Score"},
                delta={"reference": 0},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 25], "color": "lightgreen"},
                        {"range": [25, 50], "color": "yellow"},
                        {"range": [50, 75], "color": "orange"},
                        {"range": [75, 100], "color": "red"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 75,
                    },
                },
            )
        )

        fig.update_layout(height=400, template="plotly_white")

        return fig.to_html(include_plotlyjs="cdn", div_id="drift_overview")

    @staticmethod
    def _create_drift_details(drift: DatasetDrift) -> str:
        """Create detailed drift information."""
        html = f"""
        <div class='drift-summary'>
            <div class='drift-stat'>
                <span class='drift-label'>Drift Severity:</span>
                <span class='drift-value severity-{drift.drift_severity}'>{drift.drift_severity.upper()}</span>
            </div>
            <div class='drift-stat'>
                <span class='drift-label'>Columns with Drift:</span>
                <span class='drift-value'>{drift.columns_with_drift} / {drift.columns_analyzed}</span>
            </div>
            <div class='drift-stat'>
                <span class='drift-label'>Time Elapsed:</span>
                <span class='drift-value'>{drift.time_elapsed_days:.2f} days</span>
            </div>
            <div class='drift-stat'>
                <span class='drift-label'>Columns Added:</span>
                <span class='drift-value'>{len(drift.columns_added)}</span>
            </div>
            <div class='drift-stat'>
                <span class='drift-label'>Columns Removed:</span>
                <span class='drift-value'>{len(drift.columns_removed)}</span>
            </div>
        </div>
        """

        return html

    @staticmethod
    def _create_drift_charts(
        drift: DatasetDrift, baseline: DataProfile, current: DataProfile
    ) -> str:
        """Create drift comparison charts."""
        # Create drift score chart for each column
        column_names = []
        drift_scores = []
        severities = []

        for col_drift in drift.column_drifts:
            column_names.append(col_drift.column_name)
            drift_scores.append(col_drift.drift_score * 100)
            severities.append(col_drift.severity)

        # Color by severity
        colors = []
        for severity in severities:
            if severity == "critical":
                colors.append("red")
            elif severity == "high":
                colors.append("orange")
            elif severity == "medium":
                colors.append("yellow")
            elif severity == "low":
                colors.append("lightgreen")
            else:
                colors.append("lightblue")

        fig = go.Figure(
            data=[
                go.Bar(
                    x=column_names,
                    y=drift_scores,
                    marker_color=colors,
                    text=[f"{s:.1f}%" for s in drift_scores],
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="Column Drift Scores",
            xaxis_title="Column",
            yaxis_title="Drift Score (%)",
            height=500,
            template="plotly_white",
        )

        return fig.to_html(include_plotlyjs=False, div_id="drift_scores")

    @staticmethod
    def _render_template(
        title: str,
        overview: str,
        quality: str,
        columns: List[str],
        correlation: str,
        recommendations: str,
        profile: DataProfile,
    ) -> str:
        """Render HTML template for profile report."""
        template = Template(
            """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .timestamp {
            opacity: 0.9;
            font-size: 0.9em;
        }
        .section {
            background: white;
            margin-bottom: 30px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #667eea;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        h3 {
            color: #555;
            margin: 20px 0 10px 0;
        }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            background: #e0e7ff;
            color: #667eea;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: 10px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        .recommendations {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .recommendation {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .rec-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .rec-icon {
            font-size: 1.2em;
        }
        .rec-severity {
            font-weight: bold;
            text-transform: uppercase;
        }
        .rec-title {
            flex: 1;
        }
        .rec-description {
            color: #666;
            margin: 10px 0;
        }
        .rec-suggestion {
            background: #fff;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-style: italic;
        }
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="timestamp">
                Generated: {{ profile.profile_timestamp.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                Rows: {{ "{:,}".format(profile.row_count) }} |
                Columns: {{ profile.column_count }} |
                Profile Time: {{ "%.3f"|format(profile.profiling_duration_seconds) }}s
            </div>
        </header>

        <div class="section">
            <h2>Overview</h2>
            {{ overview|safe }}
        </div>

        <div class="section">
            <h2>Data Quality</h2>
            {{ quality|safe }}
        </div>

        <div class="section">
            <h2>Column Details</h2>
            {% for column_html in columns %}
                {{ column_html|safe }}
            {% endfor %}
        </div>

        {% if correlation %}
        <div class="section">
            <h2>Correlation Analysis</h2>
            {{ correlation|safe }}
        </div>
        {% endif %}

        {% if recommendations %}
        <div class="section">
            <h2>Recommendations</h2>
            {{ recommendations|safe }}
        </div>
        {% endif %}

        <footer>
            <p>Generated by Data Profiler v0.3.0 | High-Performance Data Profiling Service</p>
        </footer>
    </div>
</body>
</html>
        """
        )

        return template.render(
            title=title,
            overview=overview,
            quality=quality,
            columns=columns,
            correlation=correlation,
            recommendations=recommendations,
            profile=profile,
        )

    @staticmethod
    def _render_drift_template(
        title: str, drift_overview: str, drift_details: str, drift_charts: str, drift: DatasetDrift
    ) -> str:
        """Render HTML template for drift report."""
        template = Template(
            """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 40px 20px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .section {
            background: white;
            margin-bottom: 30px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            color: #f5576c;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }
        .drift-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .drift-stat {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #f5576c;
        }
        .drift-label {
            display: block;
            font-size: 0.9em;
            color: #666;
            margin-bottom: 8px;
        }
        .drift-value {
            display: block;
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        .severity-critical { color: #dc3545; }
        .severity-high { color: #fd7e14; }
        .severity-medium { color: #ffc107; }
        .severity-low { color: #28a745; }
        .severity-none { color: #6c757d; }
        footer {
            text-align: center;
            padding: 30px;
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="timestamp">
                Baseline: {{ drift.baseline_timestamp.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                Current: {{ drift.current_timestamp.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                Time Elapsed: {{ "%.2f"|format(drift.time_elapsed_days) }} days
            </div>
        </header>

        <div class="section">
            <h2>Drift Overview</h2>
            {{ drift_overview|safe }}
            {{ drift_details|safe }}
        </div>

        <div class="section">
            <h2>Column Drift Analysis</h2>
            {{ drift_charts|safe }}
        </div>

        <footer>
            <p>Generated by Data Profiler v0.3.0 | High-Performance Data Profiling Service</p>
        </footer>
    </div>
</body>
</html>
        """
        )

        return template.render(
            title=title,
            drift_overview=drift_overview,
            drift_details=drift_details,
            drift_charts=drift_charts,
            drift=drift,
        )
