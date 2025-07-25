"""
Report generation implementations for the String Validation Tool.

This module provides various report generators that can output validation
results in different formats (CSV, JSON, HTML).
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List
import html

from .interfaces import ReportGenerator
from .models import ValidationResult, MatchResult
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class CSVReportGenerator(ReportGenerator):
    """Generate validation reports in CSV format."""
    
    def generate_report(self, results: List[ValidationResult], output_path: str) -> None:
        """
        Generate CSV report from validation results.
        
        Args:
            results: List of validation results
            output_path: Path to output CSV file
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    "Step ID", "Screen ID", "Expected String", "OCR Output", 
                    "Match Result", "Confidence Score", "Processing Time (ms)", "Error Message"
                ])
                
                # Write results
                for result in results:
                    writer.writerow([
                        result.step.step_id,
                        result.step.screen_id,
                        result.expected_text,
                        result.ocr_output,
                        result.match_result.value,
                        f"{result.confidence_score:.3f}" if result.confidence_score is not None else "",
                        f"{result.processing_time_ms:.1f}" if result.processing_time_ms is not None else "",
                        result.error_message or ""
                    ])
            
            logger.info(f"CSV report generated: {output_path}")
            
        except Exception as e:
            raise ValidationError(f"Failed to generate CSV report: {str(e)}")
    
    def get_summary_stats(self, results: List[ValidationResult]) -> Dict:
        """Get summary statistics from results."""
        return self._calculate_summary_stats(results)
    
    def _calculate_summary_stats(self, results: List[ValidationResult]) -> Dict:
        """Calculate summary statistics."""
        if not results:
            return {
                'total_steps': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'pass_rate': 0.0,
                'average_confidence': 0.0,
                'average_processing_time_ms': 0.0,
                'results_by_type': {}
            }
        
        # Count results by type
        result_counts = {}
        for result_type in MatchResult:
            result_counts[result_type.value] = sum(
                1 for r in results if r.match_result == result_type
            )
        
        passed = result_counts.get(MatchResult.PASS.value, 0)
        failed = result_counts.get(MatchResult.FAIL.value, 0)
        errors = sum(result_counts[key] for key in result_counts if key not in [MatchResult.PASS.value, MatchResult.FAIL.value])
        
        # Calculate averages
        valid_confidence_results = [r for r in results if r.confidence_score is not None]
        avg_confidence = (
            sum(r.confidence_score for r in valid_confidence_results) / len(valid_confidence_results)
            if valid_confidence_results else 0.0
        )
        
        timed_results = [r for r in results if r.processing_time_ms is not None]
        avg_processing_time = (
            sum(r.processing_time_ms for r in timed_results) / len(timed_results)
            if timed_results else 0.0
        )
        
        return {
            'total_steps': len(results),
            'passed': passed,
            'failed': failed,
            'errors': errors,
            'pass_rate': (passed / len(results)) * 100.0,
            'average_confidence': avg_confidence,
            'average_processing_time_ms': avg_processing_time,
            'results_by_type': result_counts
        }


class JSONReportGenerator(ReportGenerator):
    """Generate validation reports in JSON format."""
    
    def generate_report(self, results: List[ValidationResult], output_path: str) -> None:
        """
        Generate JSON report from validation results.
        
        Args:
            results: List of validation results
            output_path: Path to output JSON file
        """
        try:
            report_data = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'total_results': len(results)
                },
                'summary': self.get_summary_stats(results),
                'results': []
            }
            
            # Convert results to dictionaries
            for result in results:
                result_dict = {
                    'step': {
                        'step_id': result.step.step_id,
                        'screen_id': result.step.screen_id,
                        'expected_string_id': result.step.expected_string_id
                    },
                    'expected_text': result.expected_text,
                    'ocr_output': result.ocr_output,
                    'match_result': result.match_result.value,
                    'confidence_score': result.confidence_score,
                    'processing_time_ms': result.processing_time_ms,
                    'error_message': result.error_message,
                    'is_successful': result.is_successful
                }
                report_data['results'].append(result_dict)
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"JSON report generated: {output_path}")
            
        except Exception as e:
            raise ValidationError(f"Failed to generate JSON report: {str(e)}")
    
    def get_summary_stats(self, results: List[ValidationResult]) -> Dict:
        """Get summary statistics from results."""
        csv_generator = CSVReportGenerator()
        return csv_generator.get_summary_stats(results)


class HTMLReportGenerator(ReportGenerator):
    """Generate validation reports in HTML format."""
    
    def generate_report(self, results: List[ValidationResult], output_path: str) -> None:
        """
        Generate HTML report from validation results.
        
        Args:
            results: List of validation results
            output_path: Path to output HTML file
        """
        try:
            summary = self.get_summary_stats(results)
            html_content = self._generate_html_content(results, summary)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"HTML report generated: {output_path}")
            
        except Exception as e:
            raise ValidationError(f"Failed to generate HTML report: {str(e)}")
    
    def get_summary_stats(self, results: List[ValidationResult]) -> Dict:
        """Get summary statistics from results."""
        csv_generator = CSVReportGenerator()
        return csv_generator.get_summary_stats(results)
    
    def _generate_html_content(self, results: List[ValidationResult], summary: Dict) -> str:
        """Generate HTML content for the report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OCR String Validation Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2 {{
            color: #333;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #007bff;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        .pass {{ background-color: #d4edda; color: #155724; }}
        .fail {{ background-color: #f8d7da; color: #721c24; }}
        .error {{ background-color: #fff3cd; color: #856404; }}
        .missing {{ background-color: #e2e3e5; color: #383d41; }}
        .confidence {{
            font-weight: bold;
        }}
        .high-confidence {{ color: #28a745; }}
        .medium-confidence {{ color: #ffc107; }}
        .low-confidence {{ color: #dc3545; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>OCR String Validation Report</h1>
        <p><strong>Generated:</strong> {timestamp}</p>
        
        <h2>Summary Statistics</h2>
        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{summary['total_steps']}</div>
                <div class="stat-label">Total Steps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['passed']}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['failed']}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['errors']}</div>
                <div class="stat-label">Errors</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['pass_rate']:.1f}%</div>
                <div class="stat-label">Pass Rate</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{summary['average_confidence']:.3f}</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
        </div>
        
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Step ID</th>
                    <th>Screen ID</th>
                    <th>Expected Text</th>
                    <th>OCR Output</th>
                    <th>Result</th>
                    <th>Confidence</th>
                    <th>Time (ms)</th>
                    <th>Error</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # Add result rows
        for result in results:
            result_class = self._get_result_class(result.match_result)
            confidence_class = self._get_confidence_class(result.confidence_score)
            
            confidence_display = (
                f"{result.confidence_score:.3f}" if result.confidence_score is not None else "N/A"
            )
            time_display = (
                f"{result.processing_time_ms:.1f}" if result.processing_time_ms is not None else "N/A"
            )
            
            html_content += f"""
                <tr>
                    <td>{html.escape(result.step.step_id)}</td>
                    <td>{html.escape(result.step.screen_id)}</td>
                    <td>{html.escape(result.expected_text)}</td>
                    <td>{html.escape(result.ocr_output)}</td>
                    <td class="{result_class}">{result.match_result.value}</td>
                    <td class="confidence {confidence_class}">{confidence_display}</td>
                    <td>{time_display}</td>
                    <td>{html.escape(result.error_message or "")}</td>
                </tr>
"""
        
        html_content += """
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        
        return html_content
    
    def _get_result_class(self, match_result: MatchResult) -> str:
        """Get CSS class for match result."""
        if match_result == MatchResult.PASS:
            return "pass"
        elif match_result == MatchResult.FAIL:
            return "fail"
        elif match_result == MatchResult.ERROR:
            return "error"
        else:
            return "missing"
    
    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class for confidence score."""
        if confidence is None:
            return ""
        elif confidence >= 0.8:
            return "high-confidence"
        elif confidence >= 0.5:
            return "medium-confidence"
        else:
            return "low-confidence"


class ReportGeneratorFactory:
    """Factory for creating report generators."""
    
    _generators = {
        'csv': CSVReportGenerator,
        'json': JSONReportGenerator,
        'html': HTMLReportGenerator,
    }
    
    @classmethod
    def create_generator(cls, format_type: str = 'csv') -> ReportGenerator:
        """
        Create a report generator instance.
        
        Args:
            format_type: Type of report format ('csv', 'json', 'html')
            
        Returns:
            Report generator instance
            
        Raises:
            ValueError: If format type is not supported
        """
        if format_type not in cls._generators:
            raise ValueError(f"Unsupported report format: {format_type}. "
                           f"Available formats: {list(cls._generators.keys())}")
        
        return cls._generators[format_type]()
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """Get list of available report formats."""
        return list(cls._generators.keys())