# backend/tests/test_tracked_metric.py
import pytest
from datetime import datetime
from backend.engines.tracked_metric import SourceTrace, TrackedMetric


class TestSourceTrace:
    """Tests para SourceTrace metadata"""

    def test_source_trace_creation(self):
        """Verify SourceTrace stores XBRL metadata"""
        trace = SourceTrace(
            xbrl_tag="us-gaap:NetIncomeLoss",
            raw_value=112_000_000_000,
            context_id="FY2025_Consolidated",
            extracted_at=datetime(2025, 9, 27, 10, 0, 0),
            section="income_statement"
        )

        assert trace.xbrl_tag == "us-gaap:NetIncomeLoss"
        assert trace.raw_value == 112_000_000_000
        assert trace.context_id == "FY2025_Consolidated"
        assert trace.section == "income_statement"

    def test_source_trace_to_dict(self):
        """Verify serialization to dict"""
        trace = SourceTrace(
            xbrl_tag="us-gaap:Assets",
            raw_value=352_000_000_000,
            context_id="FY2025_Instant",
            extracted_at=datetime(2025, 9, 27, 10, 0, 0),
            section="balance_sheet"
        )

        data = trace.to_dict()

        assert data['xbrl_tag'] == "us-gaap:Assets"
        assert data['raw_value'] == 352_000_000_000
        assert data['context_id'] == "FY2025_Instant"
        assert data['section'] == "balance_sheet"
        assert '2025-09-27' in data['extracted_at']  # ISO format


class TestTrackedMetric:
    """Tests para TrackedMetric con trazabilidad"""

    def test_tracked_metric_with_value(self):
        """Verify TrackedMetric encapsulates value + metadata"""
        trace_income = SourceTrace(
            xbrl_tag="us-gaap:NetIncomeLoss",
            raw_value=112_000_000_000,
            context_id="FY2025_Consolidated",
            extracted_at=datetime.now(),
            section="income_statement"
        )

        trace_equity = SourceTrace(
            xbrl_tag="us-gaap:StockholdersEquity",
            raw_value=73_700_000_000,
            context_id="FY2025_Instant",
            extracted_at=datetime.now(),
            section="balance_sheet"
        )

        metric = TrackedMetric(
            name="ROE",
            value=152.0,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={
                "net_income": trace_income,
                "equity": trace_equity
            },
            calculated_at=datetime.now()
        )

        # Test basic attributes
        assert metric.name == "ROE"
        assert metric.value == 152.0
        assert metric.unit == "%"
        assert len(metric.inputs) == 2

    def test_tracked_metric_repr(self):
        """Verify string representation"""
        metric = TrackedMetric(
            name="ROE",
            value=152.0,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={},
            calculated_at=datetime.now()
        )

        assert "ROE: 152.0%" in str(metric)

    def test_tracked_metric_null_value_repr(self):
        """Verify null value representation"""
        metric = TrackedMetric(
            name="ROE",
            value=None,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={},
            calculated_at=datetime.now()
        )

        assert "ROE: N/A" in str(metric)

    def test_tracked_metric_to_dict(self):
        """Verify serialization includes all metadata"""
        trace_income = SourceTrace(
            xbrl_tag="us-gaap:NetIncomeLoss",
            raw_value=112_000_000_000,
            context_id="FY2025_Consolidated",
            extracted_at=datetime(2025, 9, 27),
            section="income_statement"
        )

        metric = TrackedMetric(
            name="ROE",
            value=152.0,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={"net_income": trace_income},
            calculated_at=datetime(2025, 9, 27)
        )

        data = metric.to_dict()

        assert data['name'] == "ROE"
        assert data['value'] == 152.0
        assert data['unit'] == "%"
        assert data['formula'] == "(Net Income / Equity) * 100"
        assert 'net_income' in data['inputs']
        assert data['inputs']['net_income']['xbrl_tag'] == "us-gaap:NetIncomeLoss"

    def test_tracked_metric_explain_with_value(self):
        """Verify explain() generates human-readable output"""
        trace_income = SourceTrace(
            xbrl_tag="us-gaap:NetIncomeLoss",
            raw_value=112_000_000_000,
            context_id="FY2025_Consolidated",
            extracted_at=datetime.now(),
            section="income_statement"
        )

        trace_equity = SourceTrace(
            xbrl_tag="us-gaap:StockholdersEquity",
            raw_value=73_700_000_000,
            context_id="FY2025_Instant",
            extracted_at=datetime.now(),
            section="balance_sheet"
        )

        metric = TrackedMetric(
            name="ROE",
            value=152.0,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={
                "net_income": trace_income,
                "equity": trace_equity
            },
            calculated_at=datetime.now()
        )

        explanation = metric.explain()

        # Verify all components present
        assert "ROE: 152.0%" in explanation
        assert "Formula: (Net Income / Equity) * 100" in explanation
        assert "Based on:" in explanation
        assert "$112,000,000,000" in explanation
        assert "us-gaap:NetIncomeLoss" in explanation
        assert "$73,700,000,000" in explanation
        assert "us-gaap:StockholdersEquity" in explanation

    def test_tracked_metric_explain_null_value(self):
        """Verify explain() handles null values gracefully"""
        metric = TrackedMetric(
            name="ROE",
            value=None,
            unit="%",
            formula="(Net Income / Equity) * 100",
            inputs={},
            calculated_at=datetime.now()
        )

        explanation = metric.explain()

        assert "ROE: N/A (calculation failed)" in explanation
