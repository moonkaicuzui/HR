#!/usr/bin/env python3
"""
create_treemap_visualization.py - Team Employee Distribution Treemap
팀별 인원 분포 트리맵 시각화

Creates a treemap showing employee distribution by team with month-over-month changes
9월 대비 변화를 포함한 팀별 인원 분포 트리맵 생성
"""

import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))
from src.data.monthly_data_collector import MonthlyDataCollector
from src.utils.date_handler import parse_entrance_date, parse_stop_date
from src.utils.logger_config import setup_logger


class TreemapDataGenerator:
    """
    Generate treemap data for team employee distribution
    팀별 인원 분포 트리맵 데이터 생성기
    """

    # 팀별 매핑 (실제 데이터에 맞게 조정 필요)
    TEAM_MAPPING = {
        'CUTTING': ['CUTTING'],
        'STITCHING': ['STITCHING', 'Upper Inspector'],
        'ASSEMBLY': ['ASSEMBLY', 'Shoes Inspector', 'Line Leader'],
        'BOTTOM': ['BOTTOM', 'Bottom Inspector'],
        'REPACKING': ['REPACKING', 'Qip Packing Team', 'Qip Repairing'],
        'QA': ['QA', 'Qa Team', 'Audit & Training Team'],
        'OSC': ['OSC', 'Osc Inspector'],
        'MTL': ['MTL', 'Textile Tqc', 'Leather Tqc', 'Subsi Tqc', 'Happo Tqc'],
        'AQL': ['AQL', 'Qip Packing Team', 'Aql Inspector'],
        'QIP MANAGER & OFFICE & OCPT': ['QIP MANAGER', 'Repor', 'Model Master'],
        'NEW': ['신규부']
    }

    def __init__(self):
        """Initialize generator"""
        self.hr_root = Path(__file__).parent
        self.logger = setup_logger('treemap_generator', 'INFO')
        self.collector = MonthlyDataCollector(self.hr_root)

    def get_team_from_position(self, position: str) -> str:
        """
        Get team name from position
        직급에서 팀 이름 가져오기
        """
        if pd.isna(position):
            return 'UNKNOWN'

        position_str = str(position).upper()

        # Check each team mapping
        for team, positions in self.TEAM_MAPPING.items():
            for pos in positions:
                if pos.upper() in position_str:
                    return team

        return 'OTHER'

    def calculate_hierarchical_distribution(
        self,
        month: str
    ) -> Dict[str, Dict[str, int]]:
        """
        Calculate hierarchical employee distribution (team -> position)
        계층적 직원 분포 계산 (팀 -> 포지션)

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dict with team -> {position: count}
        """
        # Load data
        data = self.collector.load_month_data(month)
        df = data.get('basic_manpower', pd.DataFrame())

        if df.empty:
            self.logger.error(f"No data for {month}")
            return {}

        # Parse dates
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        # Get active employees at month end
        year, month_num = month.split('-')
        year_num = int(year)
        month_num = int(month_num)

        month_end = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + \
                   pd.DateOffset(months=1) - pd.DateOffset(days=1)

        active_df = df[
            (entrance_dates <= month_end) &
            ((stop_dates.isna()) | (stop_dates > month_end))
        ].copy()

        self.logger.info(f"{month}: {len(active_df)} active employees")

        # Count by team and position
        position_col = 'QIP POSITION 3RD  NAME'
        team_position_counts = {}

        for _, row in active_df.iterrows():
            position = row.get(position_col, '')
            team = self.get_team_from_position(position)

            if team not in team_position_counts:
                team_position_counts[team] = {}

            # Clean position name
            position_name = str(position).strip() if pd.notna(position) else 'Unknown'

            if position_name not in team_position_counts[team]:
                team_position_counts[team][position_name] = 0

            team_position_counts[team][position_name] += 1

        return team_position_counts

    def calculate_team_distribution(
        self,
        month: str
    ) -> Dict[str, int]:
        """
        Calculate employee distribution by team
        팀별 직원 분포 계산

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary of team -> employee count
        """
        # Load data
        data = self.collector.load_month_data(month)
        df = data.get('basic_manpower', pd.DataFrame())

        if df.empty:
            self.logger.error(f"No data for {month}")
            return {}

        # Parse dates
        entrance_dates = parse_entrance_date(df)
        stop_dates = parse_stop_date(df)

        # Get active employees at month end
        year, month_num = month.split('-')
        year_num = int(year)
        month_num = int(month_num)

        month_end = pd.Timestamp(f"{year_num}-{month_num:02d}-01") + \
                   pd.DateOffset(months=1) - pd.DateOffset(days=1)

        active_df = df[
            (entrance_dates <= month_end) &
            ((stop_dates.isna()) | (stop_dates > month_end))
        ].copy()

        self.logger.info(f"{month}: {len(active_df)} active employees")

        # Count by team
        team_counts = {}
        position_col = 'QIP POSITION 3RD  NAME'

        if position_col not in active_df.columns:
            self.logger.warning(f"Column '{position_col}' not found")
            return {'UNKNOWN': len(active_df)}

        for _, row in active_df.iterrows():
            position = row.get(position_col, '')
            team = self.get_team_from_position(position)

            if team not in team_counts:
                team_counts[team] = 0
            team_counts[team] += 1

        return team_counts

    def calculate_hierarchical_absence_rate(
        self,
        month: str
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate hierarchical absence rate (team -> position)
        계층적 결근율 계산 (팀 -> 포지션)

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dict with team -> {position: absence_rate}
        """
        # Load data
        data = self.collector.load_month_data(month)
        basic_df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if basic_df.empty or attendance_df.empty:
            return {}

        # Get position for each employee
        position_col = 'QIP POSITION 3RD  NAME'
        employee_positions = {}

        if position_col in basic_df.columns:
            for _, row in basic_df.iterrows():
                emp_id = str(row.get('Employee No', ''))
                position = row.get(position_col, '')
                employee_positions[emp_id] = position

        # Calculate by team and position
        team_position_absence = {}
        team_position_total = {}

        for _, row in attendance_df.iterrows():
            emp_id = str(row.get('ID No', ''))
            comp_add = row.get('compAdd', '')

            # Get position and team
            position = employee_positions.get(emp_id, '')
            position_name = str(position).strip() if pd.notna(position) else 'Unknown'
            team = self.get_team_from_position(position)

            # Initialize
            if team not in team_position_total:
                team_position_total[team] = {}
                team_position_absence[team] = {}

            if position_name not in team_position_total[team]:
                team_position_total[team][position_name] = 0
                team_position_absence[team][position_name] = 0

            team_position_total[team][position_name] += 1

            # Count absences
            if comp_add == 'Vắng mặt':
                team_position_absence[team][position_name] += 1

        # Calculate rates
        team_position_rates = {}
        for team in team_position_total:
            team_position_rates[team] = {}
            for position in team_position_total[team]:
                total = team_position_total[team][position]
                absences = team_position_absence[team][position]
                rate = (absences / total * 100) if total > 0 else 0
                team_position_rates[team][position] = round(rate, 1)

        return team_position_rates

    def calculate_absence_rate_by_team(
        self,
        month: str
    ) -> Dict[str, float]:
        """
        Calculate absence rate by team
        팀별 결근율 계산

        Args:
            month: Month in YYYY-MM format

        Returns:
            Dictionary of team -> absence rate
        """
        # Load data
        data = self.collector.load_month_data(month)
        basic_df = data.get('basic_manpower', pd.DataFrame())
        attendance_df = data.get('attendance', pd.DataFrame())

        if basic_df.empty or attendance_df.empty:
            return {}

        # Get position for each employee
        position_col = 'QIP POSITION 3RD  NAME'
        employee_positions = {}

        if position_col in basic_df.columns:
            for _, row in basic_df.iterrows():
                emp_id = str(row.get('Employee No', ''))
                position = row.get(position_col, '')
                employee_positions[emp_id] = position

        # Calculate by team
        team_absence_counts = {}
        team_total_counts = {}

        for _, row in attendance_df.iterrows():
            emp_id = str(row.get('ID No', ''))
            comp_add = row.get('compAdd', '')

            # Get team
            position = employee_positions.get(emp_id, '')
            team = self.get_team_from_position(position)

            # Initialize counts
            if team not in team_total_counts:
                team_total_counts[team] = 0
                team_absence_counts[team] = 0

            team_total_counts[team] += 1

            # Count absences
            if comp_add == 'Vắng mặt':
                team_absence_counts[team] += 1

        # Calculate rates
        team_absence_rates = {}
        for team in team_total_counts:
            if team_total_counts[team] > 0:
                rate = (team_absence_counts[team] / team_total_counts[team]) * 100
                team_absence_rates[team] = round(rate, 1)
            else:
                team_absence_rates[team] = 0.0

        return team_absence_rates

    def generate_hierarchical_treemap_data(
        self,
        current_month: str = '2025-10',
        previous_month: str = '2025-09'
    ) -> Dict:
        """
        Generate hierarchical treemap data (team -> position)
        계층적 트리맵 데이터 생성 (팀 -> 포지션)

        Returns:
            Hierarchical treemap data structure
        """
        self.logger.info(f"Generating hierarchical treemap: {previous_month} → {current_month}")

        # Get hierarchical counts
        current_hierarchy = self.calculate_hierarchical_distribution(current_month)
        previous_hierarchy = self.calculate_hierarchical_distribution(previous_month)

        # Get hierarchical absence rates
        current_absence = self.calculate_hierarchical_absence_rate(current_month)
        previous_absence = self.calculate_hierarchical_absence_rate(previous_month)

        # Build hierarchical structure
        treemap_data = {
            'name': 'Total Employees',
            'children': []
        }

        for team in sorted(current_hierarchy.keys()):
            team_positions = current_hierarchy[team]
            team_total = sum(team_positions.values())

            # Calculate team-level changes
            previous_team_total = sum(previous_hierarchy.get(team, {}).values())
            team_count_change = team_total - previous_team_total
            team_count_change_pct = (team_count_change / previous_team_total * 100) if previous_team_total > 0 else 0

            # Team-level absence rate (weighted average)
            team_absence_rate = 0
            if team in current_absence:
                total_attendance = 0
                weighted_absence = 0
                for pos, rate in current_absence[team].items():
                    count = team_positions.get(pos, 0)
                    total_attendance += count
                    weighted_absence += rate * count
                team_absence_rate = (weighted_absence / total_attendance) if total_attendance > 0 else 0

            # Build team node with position children
            team_node = {
                'name': team,
                'value': team_total,
                'absence_rate': round(team_absence_rate, 1),
                'count_change': team_count_change,
                'count_change_pct': round(team_count_change_pct, 1),
                'children': []
            }

            # Add position nodes
            for position in sorted(team_positions.keys()):
                current_count = team_positions[position]
                previous_count = previous_hierarchy.get(team, {}).get(position, 0)

                # Position-level changes
                pos_count_change = current_count - previous_count
                pos_count_change_pct = (pos_count_change / previous_count * 100) if previous_count > 0 else 0

                # Position absence rate
                pos_absence_rate = current_absence.get(team, {}).get(position, 0)
                prev_absence_rate = previous_absence.get(team, {}).get(position, 0)
                absence_change = pos_absence_rate - prev_absence_rate

                position_node = {
                    'name': position,
                    'value': current_count,
                    'absence_rate': pos_absence_rate,
                    'count_change': pos_count_change,
                    'count_change_pct': round(pos_count_change_pct, 1),
                    'absence_change': round(absence_change, 1)
                }

                team_node['children'].append(position_node)

            treemap_data['children'].append(team_node)

        return treemap_data

    def generate_treemap_data(
        self,
        current_month: str = '2025-10',
        previous_month: str = '2025-09'
    ) -> Dict:
        """
        Generate complete treemap data with changes
        변화 포함 전체 트리맵 데이터 생성

        Returns:
            Treemap data structure
        """
        self.logger.info(f"Generating treemap data: {previous_month} → {current_month}")

        # Get employee counts
        current_counts = self.calculate_team_distribution(current_month)
        previous_counts = self.calculate_team_distribution(previous_month)

        # Get absence rates
        current_absence = self.calculate_absence_rate_by_team(current_month)
        previous_absence = self.calculate_absence_rate_by_team(previous_month)

        # Build treemap structure
        treemap_data = {
            'name': 'Total Employees',
            'children': []
        }

        for team in sorted(current_counts.keys()):
            current_count = current_counts.get(team, 0)
            previous_count = previous_counts.get(team, 0)

            # Calculate changes
            count_change = current_count - previous_count
            count_change_pct = (count_change / previous_count * 100) if previous_count > 0 else 0

            # Get absence rates
            current_abs = current_absence.get(team, 0)
            previous_abs = previous_absence.get(team, 0)
            absence_change = current_abs - previous_abs
            absence_change_pct = (absence_change / previous_abs * 100) if previous_abs > 0 else 0

            team_node = {
                'name': team,
                'value': current_count,
                'absence_rate': current_abs,
                'previous_count': previous_count,
                'count_change': count_change,
                'count_change_pct': round(count_change_pct, 1),
                'absence_change': round(absence_change, 1),
                'absence_change_pct': round(absence_change_pct, 1)
            }

            treemap_data['children'].append(team_node)

        return treemap_data

    def export_to_json(self, data: Dict, output_path: Path):
        """
        Export treemap data to JSON
        트리맵 데이터를 JSON으로 내보내기
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Exported to {output_path}")

    def generate_hierarchical_html_treemap(
        self,
        data: Dict,
        output_path: Path,
        title: str = "팀별 포지션별 인원 분포"
    ):
        """
        Generate HTML file with hierarchical treemap visualization
        계층적 트리맵 시각화가 포함된 HTML 파일 생성
        """
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: -0.5px;
        }}

        .header p {{
            font-size: 16px;
            opacity: 0.9;
        }}

        .treemap-container {{
            padding: 40px;
            background: #f8f9fa;
        }}

        .treemap-wrapper {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}

        #treemap {{
            width: 100%;
            height: 800px;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            overflow: hidden;
        }}

        .team-cell {{
            stroke: white;
            stroke-width: 3px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .position-cell {{
            stroke: white;
            stroke-width: 2px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .team-cell:hover,
        .position-cell:hover {{
            opacity: 0.85;
            stroke-width: 4px;
        }}

        .team-label {{
            pointer-events: none;
            fill: white;
            font-weight: 700;
            font-size: 16px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.4);
        }}

        .position-label {{
            pointer-events: none;
            fill: white;
            font-weight: 600;
            font-size: 13px;
            text-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}

        .count-label {{
            pointer-events: none;
            fill: white;
            font-size: 28px;
            font-weight: 800;
            text-shadow: 0 2px 6px rgba(0,0,0,0.5);
        }}

        .change-label {{
            pointer-events: none;
            fill: rgba(255,255,255,0.95);
            font-size: 12px;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}

        .tooltip {{
            position: absolute;
            padding: 16px 20px;
            background: rgba(0,0,0,0.95);
            color: white;
            border-radius: 10px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 350px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            z-index: 1000;
        }}

        .tooltip-title {{
            font-weight: 700;
            font-size: 16px;
            margin-bottom: 10px;
            border-bottom: 2px solid rgba(255,255,255,0.3);
            padding-bottom: 8px;
        }}

        .tooltip-row {{
            display: flex;
            justify-content: space-between;
            margin: 6px 0;
            font-size: 13px;
        }}

        .tooltip-label {{
            opacity: 0.8;
        }}

        .tooltip-value {{
            font-weight: 600;
        }}

        .positive {{
            color: #4ade80;
        }}

        .negative {{
            color: #f87171;
        }}

        .legend {{
            margin-top: 30px;
            padding: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .legend-title {{
            font-weight: 700;
            margin-bottom: 15px;
            color: #333;
            font-size: 16px;
        }}

        .legend-gradient {{
            height: 30px;
            border-radius: 6px;
            background: linear-gradient(to right, #4ade80, #fbbf24, #f87171);
            margin-bottom: 10px;
        }}

        .legend-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>팀별 포지션별 인원 분포 및 전월 대비 변화 · Hierarchical Team & Position Distribution</p>
        </div>

        <div class="treemap-container">
            <div class="treemap-wrapper">
                <div id="treemap"></div>
            </div>

            <div class="legend">
                <div class="legend-title">결근율 색상 범례 · Absence Rate Color Scale</div>
                <div class="legend-gradient"></div>
                <div class="legend-labels">
                    <span>낮음 (Low) - 0%</span>
                    <span>보통 (Medium) - 15%</span>
                    <span>높음 (High) - 30%+</span>
                </div>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const data = {json.dumps(data, ensure_ascii=False, indent=2)};

        const width = document.getElementById('treemap').clientWidth;
        const height = document.getElementById('treemap').clientHeight;

        // Color scale for absence rate
        const colorScale = d3.scaleSequential()
            .domain([0, 30])
            .interpolator(d3.interpolateRgb("#4ade80", "#f87171"))
            .clamp(true);

        // Create treemap layout
        const treemap = d3.treemap()
            .size([width, height])
            .paddingOuter(4)
            .paddingTop(40)
            .paddingInner(3)
            .round(true);

        // Create hierarchy
        const root = d3.hierarchy(data)
            .sum(d => d.value || 0)
            .sort((a, b) => b.value - a.value);

        treemap(root);

        // Create SVG
        const svg = d3.select('#treemap')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Tooltip
        const tooltip = d3.select('#tooltip');

        // Draw cells
        const cells = svg.selectAll('g')
            .data(root.leaves())
            .enter()
            .append('g')
            .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

        // Cell rectangles
        cells.append('rect')
            .attr('class', d => d.depth === 1 ? 'team-cell' : 'position-cell')
            .attr('width', d => d.x1 - d.x0)
            .attr('height', d => d.y1 - d.y0)
            .attr('fill', d => colorScale(d.data.absence_rate || 0))
            .on('mouseover', function(event, d) {{
                tooltip.style('opacity', 1);
                updateTooltip(event, d);
            }})
            .on('mousemove', function(event, d) {{
                updateTooltip(event, d);
            }})
            .on('mouseout', function() {{
                tooltip.style('opacity', 0);
            }});

        // Labels
        cells.each(function(d) {{
            const cell = d3.select(this);
            const cellWidth = d.x1 - d.x0;
            const cellHeight = d.y1 - d.y0;

            // Only show labels if cell is large enough
            if (cellWidth > 60 && cellHeight > 40) {{
                // Name label
                cell.append('text')
                    .attr('class', d.depth === 1 ? 'team-label' : 'position-label')
                    .attr('x', cellWidth / 2)
                    .attr('y', 20)
                    .attr('text-anchor', 'middle')
                    .text(d.data.name);

                // Count label
                if (cellHeight > 60) {{
                    cell.append('text')
                        .attr('class', 'count-label')
                        .attr('x', cellWidth / 2)
                        .attr('y', cellHeight / 2 + 10)
                        .attr('text-anchor', 'middle')
                        .text(d.data.value);

                    // Change label
                    if (cellHeight > 80 && d.data.count_change !== undefined) {{
                        const changeText = d.data.count_change > 0
                            ? `+${{d.data.count_change}} (+${{d.data.count_change_pct}}%)`
                            : `${{d.data.count_change}} (${{d.data.count_change_pct}}%)`;

                        cell.append('text')
                            .attr('class', 'change-label')
                            .attr('x', cellWidth / 2)
                            .attr('y', cellHeight / 2 + 35)
                            .attr('text-anchor', 'middle')
                            .text(changeText);
                    }}
                }}
            }}
        }});

        function updateTooltip(event, d) {{
            const isTeam = d.depth === 1;
            const changeClass = (d.data.count_change || 0) >= 0 ? 'positive' : 'negative';
            const changeSymbol = (d.data.count_change || 0) >= 0 ? '▲' : '▼';

            let html = `
                <div class="tooltip-title">${{d.data.name}}</div>
                <div class="tooltip-row">
                    <span class="tooltip-label">인원:</span>
                    <span class="tooltip-value">${{d.data.value}}명</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">결근율:</span>
                    <span class="tooltip-value">${{d.data.absence_rate}}%</span>
                </div>
            `;

            if (d.data.count_change !== undefined) {{
                html += `
                    <div class="tooltip-row">
                        <span class="tooltip-label">전월 대비:</span>
                        <span class="tooltip-value ${{changeClass}}">
                            ${{changeSymbol}} ${{Math.abs(d.data.count_change)}}명 (${{d.data.count_change_pct}}%)
                        </span>
                    </div>
                `;
            }}

            if (d.data.absence_change !== undefined) {{
                const absChangeClass = d.data.absence_change >= 0 ? 'negative' : 'positive';
                html += `
                    <div class="tooltip-row">
                        <span class="tooltip-label">결근율 변화:</span>
                        <span class="tooltip-value ${{absChangeClass}}">
                            ${{d.data.absence_change > 0 ? '+' : ''}}${{d.data.absence_change}}%p
                        </span>
                    </div>
                `;
            }}

            tooltip.html(html)
                .style('left', (event.pageX + 15) + 'px')
                .style('top', (event.pageY - 15) + 'px');
        }}
    </script>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"Generated hierarchical HTML treemap: {output_path}")

    def generate_html_treemap(
        self,
        data: Dict,
        output_path: Path,
        title: str = "팀별 인원 분포 및 9월 대비 변화"
    ):
        """
        Generate HTML file with treemap visualization
        트리맵 시각화가 포함된 HTML 파일 생성
        """
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}

        #treemap {{
            width: 100%;
            height: 700px;
        }}

        .treemap-cell {{
            stroke: white;
            stroke-width: 2px;
            cursor: pointer;
            transition: opacity 0.3s;
        }}

        .treemap-cell:hover {{
            opacity: 0.8;
        }}

        .treemap-label {{
            pointer-events: none;
            fill: white;
            font-weight: 600;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}

        .treemap-value {{
            pointer-events: none;
            fill: white;
            font-size: 24px;
            font-weight: 700;
            text-shadow: 0 1px 3px rgba(0,0,0,0.4);
        }}

        .treemap-change {{
            pointer-events: none;
            fill: white;
            font-size: 12px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        }}

        .tooltip {{
            position: absolute;
            padding: 12px;
            background: rgba(0,0,0,0.9);
            color: white;
            border-radius: 6px;
            font-size: 14px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div id="treemap"></div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const data = {json.dumps(data, ensure_ascii=False)};

        // Color scale based on absence rate
        const colorScale = d3.scaleSequential()
            .domain([5, 25])
            .interpolator(d3.interpolateRgb("#4ade80", "#ef4444"));

        // Create SVG
        const width = document.getElementById('treemap').offsetWidth;
        const height = 700;

        const svg = d3.select('#treemap')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Create treemap layout
        const treemap = d3.treemap()
            .size([width, height])
            .padding(2)
            .round(true);

        // Build hierarchy
        const root = d3.hierarchy(data)
            .sum(d => d.value)
            .sort((a, b) => b.value - a.value);

        treemap(root);

        // Tooltip
        const tooltip = d3.select('#tooltip');

        // Create cells
        const cell = svg.selectAll('g')
            .data(root.leaves())
            .join('g')
            .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

        // Add rectangles
        cell.append('rect')
            .attr('class', 'treemap-cell')
            .attr('width', d => d.x1 - d.x0)
            .attr('height', d => d.y1 - d.y0)
            .attr('fill', d => colorScale(d.data.absence_rate))
            .on('mouseover', function(event, d) {{
                tooltip
                    .style('opacity', 1)
                    .html(`
                        <strong>${{d.data.name}}</strong><br>
                        인원: ${{d.data.value}}명 (${{d.data.count_change > 0 ? '+' : ''}}${{d.data.count_change}}, ${{d.data.count_change_pct > 0 ? '+' : ''}}${{d.data.count_change_pct}}%)<br>
                        결근율: ${{d.data.absence_rate}}% (${{d.data.absence_change > 0 ? '+' : ''}}${{d.data.absence_change}}%p, ${{d.data.absence_change_pct > 0 ? '+' : ''}}${{d.data.absence_change_pct}}%)
                    `)
                    .style('left', (event.pageX + 10) + 'px')
                    .style('top', (event.pageY - 10) + 'px');
            }})
            .on('mouseout', function() {{
                tooltip.style('opacity', 0);
            }});

        // Add labels
        cell.each(function(d) {{
            const g = d3.select(this);
            const cellWidth = d.x1 - d.x0;
            const cellHeight = d.y1 - d.y0;

            if (cellWidth > 80 && cellHeight > 60) {{
                // Team name
                g.append('text')
                    .attr('class', 'treemap-label')
                    .attr('x', cellWidth / 2)
                    .attr('y', 20)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', cellWidth > 150 ? '14px' : '12px')
                    .text(d.data.name);

                // Absence rate (large)
                g.append('text')
                    .attr('class', 'treemap-value')
                    .attr('x', cellWidth / 2)
                    .attr('y', cellHeight / 2 + 10)
                    .attr('text-anchor', 'middle')
                    .text(`${{d.data.absence_rate}}%`);

                // Change info
                const changeText = `${{d.data.absence_change > 0 ? '+' : ''}}${{d.data.absence_change}}% (${{d.data.absence_change_pct > 0 ? '+' : ''}}${{d.data.absence_change_pct}}%)`;
                g.append('text')
                    .attr('class', 'treemap-change')
                    .attr('x', cellWidth / 2)
                    .attr('y', cellHeight - 15)
                    .attr('text-anchor', 'middle')
                    .text(changeText);
            }} else if (cellWidth > 50 && cellHeight > 40) {{
                // Small cell - only team name
                g.append('text')
                    .attr('class', 'treemap-label')
                    .attr('x', cellWidth / 2)
                    .attr('y', cellHeight / 2)
                    .attr('text-anchor', 'middle')
                    .attr('font-size', '11px')
                    .text(d.data.name);
            }}
        }});
    </script>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"Generated HTML treemap: {output_path}")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate team distribution treemap / 팀별 분포 트리맵 생성'
    )
    parser.add_argument(
        '--current',
        type=str,
        default='2025-10',
        help='Current month (YYYY-MM) / 현재 월'
    )
    parser.add_argument(
        '--previous',
        type=str,
        default='2025-09',
        help='Previous month (YYYY-MM) / 이전 월'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        default='treemap_data.json',
        help='Output JSON file / 출력 JSON 파일'
    )
    parser.add_argument(
        '--output-html',
        type=str,
        default='treemap_visualization.html',
        help='Output HTML file / 출력 HTML 파일'
    )
    parser.add_argument(
        '--hierarchical',
        action='store_true',
        help='Generate hierarchical treemap (team -> position) / 계층적 트리맵 생성 (팀 -> 포지션)'
    )

    args = parser.parse_args()

    # Generate data
    generator = TreemapDataGenerator()

    if args.hierarchical:
        data = generator.generate_hierarchical_treemap_data(args.current, args.previous)
    else:
        data = generator.generate_treemap_data(args.current, args.previous)

    # Export
    hr_root = Path(__file__).parent
    output_dir = hr_root / 'output_files'
    output_dir.mkdir(exist_ok=True)

    # Handle absolute vs relative paths
    json_path = Path(args.output_json) if Path(args.output_json).is_absolute() or 'output_files' in args.output_json else output_dir / args.output_json
    html_path = Path(args.output_html) if Path(args.output_html).is_absolute() or 'output_files' in args.output_html else output_dir / args.output_html

    generator.export_to_json(data, json_path)

    if args.hierarchical:
        generator.generate_hierarchical_html_treemap(data, html_path)
    else:
        generator.generate_html_treemap(data, html_path)

    print(f"\n✅ Treemap generated successfully!")
    print(f"   Type: {'Hierarchical (Team → Position)' if args.hierarchical else 'Team-level only'}")
    print(f"   JSON: {json_path}")
    print(f"   HTML: {html_path}")


if __name__ == '__main__':
    main()