// Determine API Base URL dynamically
// If running locally (localhost/127.0.0.1), target local Flask server. Otherwise, use your Render production backend URL.
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:5000'
    : 'https://YOUR-BACKEND-APP-NAME.onrender.com'; // <-- REPLACE with your actual Render backend URL after deployment

// ----------------------------------------------------
// PAGE PROTECTION FLOW
// ----------------------------------------------------
(function checkAuth() {
    const isMainPage = window.location.pathname.includes("index.html") || window.location.pathname === "/" || window.location.pathname.endsWith("/");
    const user = localStorage.getItem("user");
    
    if (!user && !isMainPage) {
        // Redirect to index.html if user is not authenticated and is trying to access a page
        window.location.href = "index.html";
    }
})();

function updateNavbar() {
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;
    
    const user = localStorage.getItem("user");
    if (user) {
        // Remove existing auth elements first if any
        const existingAuth = document.getElementById('navbar-auth-item');
        if (existingAuth) existingAuth.remove();
        
        const li = document.createElement('li');
        li.id = 'navbar-auth-item';
        li.style.display = 'flex';
        li.style.alignItems = 'center';
        li.style.gap = '15px';
        li.style.marginLeft = '15px';
        li.innerHTML = `
            <span style="font-size: 0.85rem; color: var(--gold); font-weight: 500;">👤 ${user}</span>
            <a href="#" id="btnLogout" class="btn-secondary" style="padding: 4px 10px; font-size: 0.8rem; border-radius: 4px; border-color: rgba(255,255,255,0.2); color: var(--text-white);">Logout</a>
        `;
        navLinks.appendChild(li);
        
        document.getElementById('btnLogout').addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.clear();
            showToast('Logged out successfully!', 'success');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        });
    }
}

// Global Toast Utility
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'error') icon = '⚠️';
    if (type === 'success') icon = '✅';
    
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Format prices in lakhs/crores
function formatPrice(lakhs) {
    if (lakhs === null || lakhs === undefined) return 'N/A';
    if (lakhs >= 100) {
        return `₹${(lakhs / 100).toFixed(2)} Cr`;
    }
    return `₹${lakhs} Lakh`;
}

// Format timestamp
function formatTime(timestamp) {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

// ----------------------------------------------------
// 1. PREDICTOR PAGE CONTROLLER
// ----------------------------------------------------
function initPredictor() {
    const form = document.getElementById('predictionForm');
    if (!form) return;
    
    const outputCard = document.getElementById('outputCard');
    const waitingCard = document.getElementById('waitingCard');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const btn = document.getElementById('btnPredict');
        const originalText = btn.innerHTML;
        btn.innerHTML = '⚙️ Running ML Model...';
        btn.disabled = true;
        
        const payload = {
            user_email: localStorage.getItem("user"),
            chasing_team: document.getElementById('chasing_team').value,
            defending_team: document.getElementById('defending_team').value,
            target_score: Number(document.getElementById('target_score').value),
            current_score: Number(document.getElementById('current_score').value),
            completed_overs: Number(document.getElementById('completed_overs').value),
            current_over_balls: Number(document.getElementById('current_over_balls').value),
            wickets_lost: Number(document.getElementById('wickets_lost').value)
        };
        
        try {
            const response = await fetch(`${API_BASE}/api/predict`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                showToast(data.error || 'Prediction calculation failed.', 'error');
                return;
            }
            
            // Hide waiting card, show prediction
            waitingCard.style.display = 'none';
            outputCard.style.display = 'block';
            
            // Set Gauge
            const chasingProbText = document.getElementById('chasingProbText');
            const chasingTeamName = document.getElementById('chasingTeamName');
            const gaugeCircle = document.getElementById('gaugeCircle');
            
            const chasingWinPct = data.chasing_win_probability;
            chasingProbText.innerText = `${chasingWinPct}%`;
            
            // Limit team name length in gauge
            let teamAbbr = data.chasing_team;
            if (teamAbbr.length > 18) {
                teamAbbr = teamAbbr.split(' ').map(w => w[0]).join('');
            }
            chasingTeamName.innerText = teamAbbr;
            
            // Gauge animation: circumference = 2 * PI * 90 = 565
            const circumference = 565;
            const offset = circumference - (chasingWinPct / 100) * circumference;
            gaugeCircle.style.strokeDashoffset = offset;
            
            // Text Verdict
            const verdict = document.getElementById('resultVerdict');
            verdict.innerText = `${data.predicted_winner} is favored to win!`;
            if (data.predicted_winner === data.chasing_team) {
                verdict.className = "result-verdict";
                gaugeCircle.style.stroke = "var(--text-green)";
            } else {
                verdict.className = "result-verdict defending-wins";
                gaugeCircle.style.stroke = "#e04a4a";
            }
            
            // Split Labels
            document.getElementById('chasingLabel').innerText = data.chasing_team;
            document.getElementById('chasingProbVal').innerText = `${data.chasing_win_probability}%`;
            document.getElementById('defendingLabel').innerText = data.defending_team;
            document.getElementById('defendingProbVal').innerText = `${data.defending_win_probability}%`;
            
            // Stats boxes
            document.getElementById('metricRunsLeft').innerText = data.runs_left;
            document.getElementById('metricBallsLeft').innerText = data.balls_left;
            document.getElementById('metricWicketsLeft').innerText = data.wickets_left;
            document.getElementById('metricCRR').innerText = data.current_run_rate.toFixed(2);
            document.getElementById('metricRRR').innerText = data.required_run_rate.toFixed(2);
            
            showToast('Prediction generated and logged!', 'success');
            
        } catch (error) {
            console.error(error);
            showToast('Unable to connect to prediction server.', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    });
}

// ----------------------------------------------------
// 2. DASHBOARD PAGE CONTROLLER
// ----------------------------------------------------
async function initDashboard() {
    const championsCanvas = document.getElementById('championsChart');
    if (!championsCanvas) return;
    
    // Load Stats & Log list
    try {
        const statsResponse = await fetch(`${API_BASE}/api/dashboard_stats`);
        const stats = await statsResponse.json();
        
        if (statsResponse.ok) {
            // Render Champions Chart
            const champLabels = stats.champions_breakdown.map(c => c.champion);
            const champData = stats.champions_breakdown.map(c => c.titles);
            
            new Chart(championsCanvas, {
                type: 'bar',
                data: {
                    labels: champLabels,
                    datasets: [{
                        label: 'Titles Won',
                        data: champData,
                        backgroundColor: 'rgba(212, 175, 55, 0.65)',
                        borderColor: 'rgba(212, 175, 55, 0.95)',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1, color: '#94a3b8' },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        },
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
            
            // Render Run Trends Chart
            const seasonLabels = stats.season_trends.map(s => s.season);
            const seasonRuns = stats.season_trends.map(s => s.total_runs);
            const seasonSixes = stats.season_trends.map(s => s.sixes);
            
            const trendsCanvas = document.getElementById('runTrendsChart');
            new Chart(trendsCanvas, {
                type: 'line',
                data: {
                    labels: seasonLabels,
                    datasets: [
                        {
                            label: 'Total Runs',
                            data: seasonRuns,
                            borderColor: '#3cd070',
                            backgroundColor: 'rgba(60, 208, 112, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Sixes Hit',
                            data: seasonSixes,
                            borderColor: '#d4af37',
                            backgroundColor: 'rgba(212, 175, 55, 0.1)',
                            borderWidth: 2,
                            fill: false,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            position: 'left',
                            ticks: { color: '#3cd070' },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        },
                        y1: {
                            position: 'right',
                            ticks: { color: '#d4af37' },
                            grid: { display: false }
                        },
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { display: false }
                        }
                    },
                    plugins: {
                        legend: { labels: { color: '#94a3b8' } }
                    }
                }
            });
        }
        
        // Fetch logs list from correct route /api/history filtered by user session email
        const user = localStorage.getItem("user");
        const logsResponse = await fetch(`${API_BASE}/api/history?user_email=${encodeURIComponent(user || '')}`);
        const logs = await logsResponse.json();
        
        const logsTable = document.getElementById('logsTableBody');
        if (logsResponse.ok && logs.length > 0) {
            logsTable.innerHTML = '';
            // Show only first 10
            logs.slice(0, 10).forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-size: 0.8rem; color: var(--text-muted);">${formatTime(log.created_at)}</td>
                    <td style="font-weight: 600;">${log.chasing_team}</td>
                    <td>${log.defending_team}</td>
                    <td style="color: var(--gold); font-weight: 600;">${log.target_score}</td>
                    <td>${log.current_score} <span style="color: var(--text-muted); font-size: 0.8rem;">(Balls left: ${log.balls_left})</span></td>
                    <td>${log.wickets_lost}</td>
                    <td style="color: var(--text-green); font-weight: 700;">${log.chasing_win_probability}%</td>
                    <td><span class="btn-secondary" style="padding: 2px 8px; font-size: 0.75rem; border-radius: 4px; pointer-events: none;">${log.predicted_winner}</span></td>
                `;
                logsTable.appendChild(tr);
            });
        } else {
            logsTable.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No prediction history found. Use the predictor tool to log simulations!</td></tr>`;
        }
        
    } catch (error) {
        console.error("Dashboard failed to initialize:", error);
        showToast('Failed to load dashboard visualizations.', 'error');
    }
}

// ----------------------------------------------------
// 3. PLAYERS PAGE CONTROLLER (Client-Side Search/Paging)
// ----------------------------------------------------
let allPlayers = [];
let filteredPlayers = [];
let playerCurrentPage = 1;
const playersPerPage = 25;

function displayPlayers() {
    const tbody = document.getElementById('playersTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (filteredPlayers.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">No players match search criteria.</td></tr>`;
        document.getElementById('btnPrevPage').disabled = true;
        document.getElementById('btnNextPage').disabled = true;
        document.getElementById('pageInfo').innerText = 'Showing 0-0 of 0';
        return;
    }
    
    const startIndex = (playerCurrentPage - 1) * playersPerPage;
    const endIndex = Math.min(startIndex + playersPerPage, filteredPlayers.length);
    const pageItems = filteredPlayers.slice(startIndex, endIndex);
    
    pageItems.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight: 600;">${p.player_name}</td>
            <td>${p.nationality}</td>
            <td><span class="btn-primary" style="padding: 2px 8px; font-size: 0.75rem; border-radius: 4px; pointer-events: none; background: rgba(255,255,255,0.05); color: var(--text-white); border: 1px solid var(--border-color);">${p.playing_role}</span></td>
            <td style="font-size: 0.9rem; color: var(--text-muted);">${p.batting_style || 'Not Specified'}</td>
            <td style="font-size: 0.9rem; color: var(--text-muted);">${p.bowling_style || 'Not Specified'}</td>
            <td>${p.ipl_debut_season || '--'}</td>
            <td style="font-weight: 600;">${formatPrice(p.base_price_lakh)}</td>
            <td style="color: var(--gold); font-weight: 700;">${formatPrice(p.highest_auction_price_lakh)}</td>
        `;
        tbody.appendChild(tr);
    });
    
    // Update Pagination UI
    document.getElementById('pageInfo').innerText = `Showing ${startIndex + 1}-${endIndex} of ${filteredPlayers.length} players`;
    document.getElementById('btnPrevPage').disabled = playerCurrentPage <= 1;
    document.getElementById('btnNextPage').disabled = endIndex >= filteredPlayers.length;
}

function filterAndDisplayPlayers() {
    const searchVal = document.getElementById('searchPlayer').value.toLowerCase().trim();
    const roleVal = document.getElementById('filterRole').value;
    const nationalityVal = document.getElementById('filterNationality').value;
    
    filteredPlayers = allPlayers.filter(p => {
        const matchesSearch = p.player_name.toLowerCase().includes(searchVal);
        
        let matchesRole = true;
        if (roleVal !== 'All') {
            matchesRole = p.playing_role === roleVal;
        }
        
        let matchesNationality = true;
        if (nationalityVal !== 'All') {
            if (nationalityVal === 'Indian') {
                matchesNationality = p.nationality === 'India';
            } else if (nationalityVal === 'Overseas') {
                matchesNationality = p.nationality !== 'India';
            }
        }
        
        return matchesSearch && matchesRole && matchesNationality;
    });
    
    playerCurrentPage = 1;
    displayPlayers();
}

async function loadPlayers() {
    const tbody = document.getElementById('playersTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--text-muted);">Fetching players roster...</td></tr>`;
    
    try {
        const response = await fetch(`${API_BASE}/api/players`);
        const data = await response.json();
        
        if (response.ok) {
            allPlayers = data;
            filteredPlayers = allPlayers;
            displayPlayers();
        } else {
            showToast('Error loading players database.', 'error');
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #e04a4a;">Connection error. Could not reach server.</td></tr>`;
    }
}

function initPlayers() {
    const search = document.getElementById('searchPlayer');
    if (!search) return;
    
    // Bind search and filter triggers
    let debounceTimer;
    search.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            filterAndDisplayPlayers();
        }, 250);
    });
    
    document.getElementById('filterRole').addEventListener('change', filterAndDisplayPlayers);
    document.getElementById('filterNationality').addEventListener('change', filterAndDisplayPlayers);
    
    // Pagination buttons
    document.getElementById('btnPrevPage').addEventListener('click', () => {
        if (playerCurrentPage > 1) {
            playerCurrentPage--;
            displayPlayers();
        }
    });
    
    document.getElementById('btnNextPage').addEventListener('click', () => {
        const maxPages = Math.ceil(filteredPlayers.length / playersPerPage);
        if (playerCurrentPage < maxPages) {
            playerCurrentPage++;
            displayPlayers();
        }
    });
    
    loadPlayers();
}

// ----------------------------------------------------
// 4. SEASONS PAGE CONTROLLER
// ----------------------------------------------------
async function initSeasons() {
    const tbody = document.getElementById('seasonsTableBody');
    if (!tbody) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/seasons`);
        const seasons = await response.json();
        
        if (response.ok) {
            tbody.innerHTML = '';
            seasons.forEach(s => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight: 700; color: var(--gold);">${s.season}</td>
                    <td>${s.num_teams}</td>
                    <td>${s.total_matches}</td>
                    <td style="font-weight: 600; color: var(--text-green);">${s.champion}</td>
                    <td>${s.runner_up}</td>
                    <td>${s.total_runs_scored ? s.total_runs_scored.toLocaleString() : '--'}</td>
                    <td>${s.total_sixes ? s.total_sixes.toLocaleString() : '--'}</td>
                    <td>${s.total_fours ? s.total_fours.toLocaleString() : '--'}</td>
                    <td>${s.avg_first_innings_score ? s.avg_first_innings_score.toFixed(1) : '--'}</td>
                    <td>${s.highest_team_total || '--'}</td>
                    <td>${s.lowest_team_total || '--'}</td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            showToast('Failed to load seasons recap list.', 'error');
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: #e04a4a;">Network error. Could not connect to API.</td></tr>`;
    }
}

// Global page initializer
window.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
    initPredictor();
    initDashboard();
    initPlayers();
    initSeasons();
});
