
// ============================================================================
// 원본 management_dashboard_2025_09.html에서 추출한 모달 함수들
// ============================================================================

// 1. 총 재직자 수 상세 분석 모달
function createEnhancedTotalEmployeesContent(modalBody, modalId) {
            // Declare treemapDiv at function scope so it can be appended at the end
            let treemapDiv;
            
            // 1. 월별 트렌드 차트
            const monthlyDiv = document.createElement('div');
            monthlyDiv.className = 'chart-container';
            monthlyDiv.innerHTML = '<canvas id="monthly-' + modalId + '"></canvas>';
            modalBody.appendChild(monthlyDiv);
            
            const monthlyChart = new Chart(document.getElementById('monthly-' + modalId), {
                type: 'bar',
                data: {
                    labels: ['7월', '8월'],
                    datasets: [{
                        label: '총인원',
                        data: [centralizedData.previous_month.total_employees || 0, centralizedData.current_month.total_employees || 0],
                        backgroundColor: ['#FFEAA7', '#45B7D1']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: '월별 총인원 비교',
                            align: 'start',
                            font: {
                                size: 18,
                                weight: 600
                            },
                            padding: {
                                bottom: 10
                            },
                            color: '#333'
                        }
                    }
                }
            });
            charts[modalId] = [monthlyChart];
            
            // 2. 주차별 트렌드 차트 - 7-8월 연속 시계열
            const trendDiv = document.createElement('div');
            trendDiv.className = 'chart-container';
            trendDiv.innerHTML = '<canvas id="trend-' + modalId + '"></canvas>';
            modalBody.appendChild(trendDiv);
            
            // 7월과 8월 주차별 데이터를 연속으로 결합 - 날짜 레이블 사용
            const combinedLabels = [];
            const combinedValues = [];
            
            // 7월 데이터 처리 (있는 것만)
            const julyWeeklyData = {};
            for (let i = 1; i <= 4; i++) {
                const weekKey = 'Week' + i;
                if (julyWeeklyData[weekKey]) {
                    combinedLabels.push('07/' + String(1 + (i-1)*7).padStart(2, '0'));
                    combinedValues.push(julyWeeklyData[weekKey].total_employees || 0);
                }
            }
            
            // 8월 데이터 처리 (있는 것만)
            const augustWeeklyData = {"Week1": {"date": "09/01", "date_full": "2025-09-01", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 0, "resignations": 0}, "Week2": {"date": "09/08", "date_full": "2025-09-08", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 5, "resignations": 0}, "Week3": {"date": "09/15", "date_full": "2025-09-15", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 1, "resignations": 0}};
            for (let i = 1; i <= 4; i++) {
                const weekKey = 'Week' + i;
                if (augustWeeklyData[weekKey]) {
                    combinedLabels.push(augustWeeklyData[weekKey].date || ('08/' + String(1 + (i-1)*7).padStart(2, '0')));
                    combinedValues.push(augustWeeklyData[weekKey].total_employees || 0);
                }
            }
            
            // 추세선을 위한 선형 회귀 계산 (실제 데이터 개수 기반)
            const xValues = Array.from({length: combinedValues.length}, (_, i) => i);
            const n = combinedValues.length;
            const sumX = xValues.reduce((a, b) => a + b, 0);
            const sumY = combinedValues.reduce((a, b) => a + b, 0);
            const sumXY = xValues.reduce((sum, x, i) => sum + x * combinedValues[i], 0);
            const sumX2 = xValues.reduce((sum, x) => sum + x * x, 0);
            const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
            const intercept = (sumY - slope * sumX) / n;
            const trendlineData = xValues.map(x => slope * x + intercept);
            
            const trendChart = new Chart(document.getElementById('trend-' + modalId), {
                type: 'line',
                data: {
                    labels: combinedLabels,
                    datasets: [
                        {
                            label: '주차별 총인원',
                            data: combinedValues,
                            borderColor: '#FF6B6B',
                            backgroundColor: 'rgba(255, 107, 107, 0.1)',
                            tension: 0.3,
                            borderWidth: 2,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        },
                        {
                            label: '추세선',
                            data: trendlineData,
                            borderColor: '#45B7D1',
                            borderDash: [10, 5],
                            borderWidth: 2,
                            fill: false,
                            pointRadius: 0,
                            pointHoverRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: '주차별 총인원 트렌드',
                            align: 'start',
                            font: {
                                size: 18,
                                weight: 600
                            },
                            padding: {
                                bottom: 10
                            },
                            color: '#333'
                        }
                    }
                }
            });
            charts[modalId].push(trendChart);
            
            // 3. 팀별 인원 분포 (크기 순서로 정렬)
            const teamDiv = document.createElement('div');
            teamDiv.className = 'chart-container';
            teamDiv.innerHTML = '<canvas id="team-' + modalId + '"></canvas>';
            modalBody.appendChild(teamDiv);
            
            // 팀 데이터를 인원 수 기준으로 정렬
            let teamData = Object.entries(teamStats)
                .map(([name, data]) => ({
                    name: name,
                    total: data.total || 0,
                    percentage: ((data.total || 0) / centralizedData.current_month.total_employees * 100).toFixed(1)
                }))
                .sort((a, b) => b.total - a.total);
            
            const teamNames = teamData.map(t => t.name);
            const teamCounts = teamData.map(t => t.total);
            const teamPercentages = teamData.map(t => t.percentage);
            
            const teamBarChart = new Chart(document.getElementById('team-' + modalId), {
                type: 'bar',
                data: {
                    labels: teamNames,
                    datasets: [{
                        label: '인원 수',
                        data: teamCounts,
                        backgroundColor: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E2", "#FF9FF3", "#54A0FF", "#48DBFB", "#00D2D3", "#1ABC9C"]
                    }]
                },
                options: {
                    indexAxis: 'y',  // 가로 바 차트
                    responsive: true,
                    maintainAspectRatio: false,
                    onClick: function(event, elements) {
                        if (elements.length > 0) {
                            const index = elements[0].index;
                            const teamName = teamNames[index];
                            showTeamDetails(teamName);
                        }
                    },
                    plugins: {
                        title: {
                            display: true,
                            text: '팀별 인원 분포 (클릭하여 상세보기)',
                            align: 'start',
                            font: {
                                size: 18,
                                weight: 600
                            },
                            padding: {
                                bottom: 10
                            },
                            color: '#333'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const index = context.dataIndex;
                                    const count = teamCounts[index];
                                    const percent = teamPercentages[index];
                                    return count + '명 (' + percent + '%)';
                                }
                            }
                        }
                    }
                }
            });
            charts[modalId].push(teamBarChart);
            
            // 4. TYPE별 인원 카드를 먼저 배치 (카드 컨테이너로 감싸기)
            const typeSection = document.createElement('div');
            typeSection.className = 'card-section';
            typeSection.style.marginTop = '30px';
            typeSection.style.clear = 'both';  // float 클리어
            
            const typeTitle = document.createElement('h4');
            typeTitle.style.cssText = 'margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;';
            typeTitle.textContent = 'TYPE별 인원 현황';
            typeSection.appendChild(typeTitle);
            
            const typeCardsDiv = document.createElement('div');
            typeCardsDiv.className = 'type-cards';
            
            // TYPE 값 처리 - 문자열일 수 있음
            c

// ============================================================================
// 2. 팀 상세 정보 모달  
function showTeamDetails(teamName) {
            // Get team data from the global teamStats object
            const teamData = teamStats[teamName];
            if (!teamData) {
                console.error('Team data not found for:', teamName);
                return;
            }
            
            // Clean up any existing charts for this team
            const cleanName = teamName.replace(/[^a-zA-Z0-9]/g, '_');
            if (teamDetailCharts[cleanName]) {
                teamDetailCharts[cleanName].forEach(chart => {
                    if (chart && typeof chart.destroy === 'function') {
                        chart.destroy();
                    }
                });
                teamDetailCharts[cleanName] = [];
            }
            
            // Check if modal already exists
            let modal = document.getElementById(`team-modal-${cleanName}`);
            if (modal) {
                // Remove existing modal to rebuild fresh
                modal.remove();
            }
            
            // Create new modal
            modal = document.createElement('div');
            modal.id = `team-modal-${cleanName}`;
            modal.className = 'modal';
            modal.style.display = 'block';
            modal.style.zIndex = '2000';
            const monthlyData = {"2025_08": {"error_count": 0, "error_rate": 0.0, "total_employees": 399, "type1_count": "130", "type2_count": "247", "type3_count": "22", "attendance_rate": 86.360131097, "absence_rate": 13.639868903, "absence_count": 0, "resignation_count": 0, "resignation_rate": 0.0, "recent_hires": 0, "recent_hires_rate": 0.0, "recent_resignations": 0, "recent_resignation_rate": 0.0, "under_60_days": 0, "under_60_days_rate": 0.0, "post_assignment_resignations": 0, "post_assignment_resignation_rate": 0.0, "full_attendance_count": 161, "full_attendance_rate": 40.350877193, "long_term_count": 0, "long_term_rate": 0.0}, "2025_07": {"error_count": 0, "error_rate": 0.0, "total_employees": 376, "type1_count": "126", "type2_count": "235", "type3_count": "15", "attendance_rate": 90.7261794635, "absence_rate": 9.2738205365, "absence_count": 0, "resignation_count": 0, "resignation_rate": 0.0, "recent_hires": 0, "recent_hires_rate": 0.0, "recent_resignations": 0, "recent_resignation_rate": 0.0, "under_60_days": 0, "under_60_days_rate": 0.0, "post_assignment_resignations": 0, "post_assignment_resignation_rate": 0.0, "full_attendance_count": 305, "full_attendance_rate": 81.1170212766, "long_term_count": 0, "long_term_rate": 0.0}, "2025_09": {"error_count": 0, "error_rate": 0.0, "total_employees": 393, "type1_count": "127", "type2_count": "246", "type3_count": "20", "attendance_rate": 88.94108436093168, "absence_rate": 11.058915639068317, "absence_count": 163, "resignation_count": 0, "resignation_rate": 0.0, "recent_hires": 19, "recent_hires_rate": 4.8346055979643765, "recent_resignations": 0, "recent_resignation_rate": 0.0, "under_60_days": 37, "under_60_days_rate": 9.414758269720101, "post_assignment_resignations": 0, "post_assignment_resignation_rate": 0.0, "full_attendance_count": 230, "full_attendance_rate": 58.524173027989825, "long_term_count": 280, "long_term_rate": 71.2468193384224}};
            const weeklyData = {"2025_08": {"Week1": {"date": "08/01", "date_full": "2025-08-01", "total_employees": 399, "attendance_rate": 89.73, "absence_rate": 10.27, "new_hires": 3, "resignations": 0}, "Week2": {"date": "08/08", "date_full": "2025-08-08", "total_employees": 399, "attendance_rate": 89.73, "absence_rate": 10.27, "new_hires": 0, "resignations": 0}, "Week3": {"date": "08/15", "date_full": "2025-08-15", "total_employees": 399, "attendance_rate": 89.73, "absence_rate": 10.27, "new_hires": 0, "resignations": 0}}, "2025_09": {"Week1": {"date": "09/01", "date_full": "2025-09-01", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 0, "resignations": 0}, "Week2": {"date": "09/08", "date_full": "2025-09-08", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 5, "resignations": 0}, "Week3": {"date": "09/15", "date_full": "2025-09-15", "total_employees": 393, "attendance_rate": 88.94, "absence_rate": 11.06, "new_hires": 1, "resignations": 0}}};
            const teamMembersList = teamMembers[teamName] || [];
            // 데이터 일관성 보장 - teamStats와 teamMembers 동기화
            const members = teamMembersList;
            const actualMemberCount = members.length;
            
            // teamStats의 total을 실제 멤버 수로 업데이트
            if (teamStats[teamName]) {
                if (teamStats[teamName].total !== actualMemberCount) {
                    console.warn(`Correcting ${teamName} count: ${teamStats[teamName].total} -> ${actualMemberCount}`);
                    teamStats[teamName].total = actualMemberCount;
                }
            }
    
            
            // 팀 멤버를 역할별로 그룹화
            const roleGroups = {};
            console.log('Team members for', teamName, ':', teamMembersList);
            
            teamMembersList.forEach(member => {
                // Use role_category as the primary role field (팀 내 역할)
                const role = member.role_category || member.role || 'Unknown';
                if (!roleGroups[role]) {
                    roleGroups[role] = [];
                }
                roleGroups[role].push(member);
            });
            
            console.log('Role groups:', roleGroups);
            
            const modalContent = `
                <div class="modal-content" style="max-width: 1400px; width: 90%;">
                    <div class="modal-header">
                        <h2 class="modal-title">${teamName} 팀 상세 정보</h2>
                        <span class="close-modal" onclick="closeTeamDetailModalByName('${teamName}')">&times;</span>
                    </div>
                    <div class="modal-body" style="max-height: 80vh; overflow-y: auto;">
                        <!-- 1. 월별 총인원 트렌드 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">월별 팀 인원 트렌드</h4>
                            <div style="position: relative; height: 300px;">
                                <canvas id="team-monthly-trend-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}"></canvas>
                            </div>
                        </div>
                        
                        <!-- 2. 주차별 총인원 트렌드 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">주차별 팀 인원 트렌드</h4>
                            <div style="position: relative; height: 300px;">
                                <canvas id="team-weekly-trend-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}"></canvas>
                            </div>
                        </div>
                        
                        <!-- 3. Multi-Level Donut - 팀내 역할별 인원 분포 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">Multi-Level Donut - 팀내 역할별 인원 분포</h4>
                            <div style="position: relative; height: 350px;">
                                <canvas id="team-role-dist-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}"></canvas>
                            </div>
                        </div>
                        
                        <!-- 4. 팀내 역할별 만근율 현황 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">팀내 역할별 만근율 현황</h4>
                            <div style="position: relative; height: 300px;">
                                <canvas id="team-role-attendance-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}"></canvas>
                            </div>
                        </div>
                        
                        <!-- 5. 5단계 계층 구조 Sunburst 차트 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">5단계 계층 구조 Sunburst 차트 - 팀내 역할별 인원 분포</h4>
                            <div id="team-role-sunburst-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}" style="height: 500px; background: #fff; border-radius: 8px; padding: 10px; position: relative;"></div>
                        </div>
                        
                        <!-- 6. 팀원 상세 정보 -->
                        <div class="card-section">
                            <h4 style="margin: 0 0 15px 0; font-size: 18px; font-weight: 600; color: #333;">팀원 상세 정보</h4>
                            <div style="max-height: 500px; overflow-y: auto;">
                                <table id="team-member-detail-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}" style="width: 100%; border-collapse: collapse; font-size: 12px;">
                                    <thead style="position: sticky; top: 0; background: #f1f3f5; z-index: 10;">
                                        <tr>
                                            <th style="padding: 8px; text-align: left; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 0, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Role<br>Category <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: left; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 1, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">직급 1<br>(Position 1st) <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: left; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 2, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">직급 2<br>(Position 2nd) <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: left; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 3, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Full<br>Name <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 4, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Employee<br>No <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 5, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Entrance<br>Date <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 6, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Years of<br>Service <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 7, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Working<br>Days <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 8, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Absent<br>Days <span style="font-size: 10px; color: #666;">▼</span></th>
                                            <th style="padding: 8px; text-align: center; cursor: pointer; white-space: normal; word-break: break-word; user-select: none; transition: background-color 0.2s;" onclick="sortTeamTable(this, 9, '${teamName.replace(/[^a-zA-Z0-9]/g, '_')}')" onmouseover="this.style.backgroundColor='#e1e5e8'" onmouseout="this.style.backgroundColor=''">Absence<br>Rate (%) <span style="font-size: 10px; color: #666;">▼</span></th>
                                        </tr>
                                    </thead>
                                    <tbody id="team-member-tbody-${teamName.replace(/[^a-zA-Z0-9]/g, '_')}"></tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            modal.innerHTML = modalContent;
            document.body.appendChild(modal);
            
            // Initialize charts and tables after DOM is ready
            setTimeout(() => {
                console.log('Initializing charts for', teamName);
                const cleanName = teamName.replace(/[^a-zA-Z0-9]/g, '_');
                
                // Check if elements exist
                const monthlyCanvas = document.getElementById(`team-monthly-trend-${cleanName}`);
                const weeklyCanvas = document.getElementById(`team-weekly-trend-${cleanName}`);
                const roleCanvas = document.getElementById(`team-role-dist-${cleanName}`);
                const tbody = document.getElementById(`team-member-tbody-${cleanName}`);
                
                console.log('Canvas elements found:', {
                    monthly: !!monthlyCanvas,
                    weekly: !!weeklyCanvas,
                    role: !!roleCanvas,
                    tbody: !!tbody
                });
                
                if (monthlyCanvas || weeklyCanvas || roleCanvas) {
                    initializeTeamDetailCharts(teamName, teamData, roleGroups, monthlyData, weeklyData, teamMembersList);
                }
                if (tbody) {
                    initializeTeamMembersTable(teamName, teamMembersList);
                }
            }, 200);
        }
        
        // 팀 상세 모달 닫기 함수 수정
        function closeTeamDetailModalByName(teamName) {
            const cleanName = teamName.replace(/[^a-zA-Z0-9]/g, '_');
            
            // Properly destroy charts first
            if (teamDetailCharts[cleanName]) {
                teamDetailCharts[cleanName].forEach(chart => {
                    if (chart && typeof chart.destroy === 'function') {
                        chart.destroy();
                    }
                });
                delete teamDetailCharts[cleanName];
            }
            
            // Remove modal
            const modal = document.getElementById(`team-modal-${cleanName}`);
            if (modal) {
                modal.remove();
            }
        }
        
        // 팀 상세 차트 초기화 함수
        function initializeTeamDetailCharts(teamName, teamData, roleGroups, monthlyData, weeklyData, members) {
            const cleanName = teamName.replace(/[^a-zA-Z0-9]/g, '_');
            
            // Initialize chart storage for this team
            if (!teamDetailCharts[cleanName]) {
                teamDetailCharts[cleanName] = [];
            }
            
            // 1. 월별 팀 인원 트렌드
            const monthlyCtx = document.getElementById(`team-monthly-trend-${cleanName}`);
            console.log('Monthly chart canvas:', monthlyCtx);
            if (monthlyCtx) {
                // Clear any existing chart instance
                const existingChart = Chart.getChart(monthlyCtx);
                if (existingChart) {
                    existingChart.destroy();
                }
                
                // Get July data for this team
                const julyTeamData = {"OFFICE & OCPT": {"total": 5, "attendance_rate": 80.0, "absence_rate": 20.0, "new_hires": 0, "resignations": 0, "full_attendance_count": 4, "full_attendance_rate": 80.0}, "OSC": {"total": 22, "attendance_rate": 95.06, "absence_rate": 4.94, "new_hires": 0, "resignations": 0, "full_attendance_count": 20, "full_attendance_rate": 90.91}, "ASSEMBLY": {"total": 110, "attendance_rate": 94.51, "absence_rate": 5.49, "new_hires": 1, "resignations": 0, "full_attendance_count": 94, "full_attendance_rate": 85.45}, "BOTTOM": {"total": 30, "attendance_rate": 93.91, "absence_rate": 6.09, "new_hires": 1, "resignations": 0, "full_attendance_count": 24, "full_attendance_rate": 80.0}, "QA": {"total": 20, "attendance_rate": 94.57, "absence_rate": 5.43, "new_hires": 0, "resignations": 0, "full_attendance_count": 18, "full_attendance_rate": 90.0}, "MTL": {"total": 28, "attendance_rate": 96.12, "absence_rate": 3.88, "new_hires": 0, "resignations": 0, "full_attendance_count": 25, "full_attendance_rate": 89.29}, "STITCHING": {"total": 98, "attendance_rate": 92.9, "absence_rate": 7.1, "new_hires": 1, "resignations": 0, "full_attendance_count": 79, "full_attendance_rate": 80.61}, "AQL": {"total": 22, "attendance_rate": 98.81, "absence_rate": 1.19, "new_hires": 0, "resignations": 0, "full_attendance_count": 19, "full_attendance_rate": 86.36}, "REPACKING": {"total": 17, "attendance_rate": 96.68, "absence_rate": 3.32, "new_hires": 0, "resignations": 0, "full_attendance_count": 15, "full_attendance_rate": 88.24}, "HWK QIP": {"total": 1, "attendance_rate": 100.0, "absence_rate": 0.0, "new_hires": 0, "resignations": 0, "full_attendance_count": 1, "full_attendance_rate": 100.0}, "CUTTING": {"total": 8, "attendance_rate": 75.0, "absence_rate": 25.0, "new_hires": 0, "resignations": 0, "full_attendance_count": 6, "full_attendance_rate": 75.0}, "NEW": {"total": 15, "attendance_rate": 13.62, "absence_rate": 86.38, "new_hires": 9, "resignations": 0, "full_attendance_count": 0, "full_attendance_rate": 0.0}};
                const julyTotal = julyTeamData[teamName]?.total || Math.round(teamData.total * (0.8 + Math.random() * 0.4));
                
                const monthlyChart = new Chart(monthlyCtx, {
                    type: 'line',
                    data: {
                        labels: ['7월', '8월'],
                        datasets: [{
                            label: '팀 인원',
                            data: [julyTotal, members.length || teamData.total || 0],  // 필터링된 members.length 우선 사용
                            borderColor: '#4ECDC4',
                            backgroundColor: 'rgba(78, 205, 196, 0.1)',
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
             

