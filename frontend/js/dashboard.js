/**
 * PHC AI Assistant - Dashboard JavaScript
 * Handles all dashboard page functionality with improved loading and error handling
 */

// ============================================
// CONFIGURATION
// ============================================

const API_BASE = 'http://localhost:8000';
const API_TIMEOUT = 30000; // 30 seconds timeout
const RETRY_DELAY = 2000; // 2 seconds between retries

// Dashboard State
let dashboardData = null;
let loadingTimeout = null;

// ============================================
// API CALL WITH TIMEOUT
// ============================================

async function apiCallWithTimeout(endpoint, timeout = API_TIMEOUT) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            signal: controller.signal,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
        
    } catch (error) {
        clearTimeout(timeoutId);
        
        if (error.name === 'AbortError') {
            throw new Error('Request timed out. Server may be loading models (this can take 2-3 minutes on first run).');
        }
        
        throw error;
    }
}

// ============================================
// LOADING STATES
// ============================================

function showLoading(containerId, message = 'Loading...', subMessage = null) {
    const container = document.getElementById(containerId);
    
    // Clear any existing timeout
    if (loadingTimeout) {
        clearTimeout(loadingTimeout);
    }
    
    let timeElapsed = 0;
    const startTime = Date.now();
    
    const loadingHTML = `
        <div style="text-align: center; padding: 100px 20px;">
            <div class="spinner" style="margin: 0 auto 20px;"></div>
            <h3 style="color: var(--dark); margin-bottom: 10px;">${message}</h3>
            ${subMessage ? `<p style="color: var(--gray); font-size: 14px; margin-bottom: 15px;">${subMessage}</p>` : ''}
            <p id="loading-timer" style="color: var(--gray); font-size: 13px;">Time elapsed: 0s</p>
            <p style="color: var(--gray); font-size: 12px; margin-top: 20px; max-width: 500px; margin-left: auto; margin-right: auto;">
                💡 <strong>First-time setup:</strong> Loading AI models can take 2-3 minutes. Subsequent loads will be faster!
            </p>
        </div>
    `;
    
    container.innerHTML = loadingHTML;
    
    // Update timer every second
    loadingTimeout = setInterval(() => {
        timeElapsed = Math.floor((Date.now() - startTime) / 1000);
        const timerEl = document.getElementById('loading-timer');
        if (timerEl) {
            timerEl.textContent = `Time elapsed: ${timeElapsed}s`;
            
            // Add helpful messages at certain intervals
            if (timeElapsed === 30) {
                timerEl.innerHTML += '<br><span style="color: #f59e0b;">⏳ Still loading... This is normal for first run.</span>';
            } else if (timeElapsed === 60) {
                timerEl.innerHTML += '<br><span style="color: #f59e0b;">⏳ Almost there... Loading translation models.</span>';
            } else if (timeElapsed > 90) {
                timerEl.innerHTML += '<br><span style="color: #ef4444;">⚠️ Taking longer than expected. Check backend logs.</span>';
            }
        }
    }, 1000);
}

function showError(containerId, message, canRetry = true) {
    // Clear loading timeout
    if (loadingTimeout) {
        clearTimeout(loadingTimeout);
    }
    
    const container = document.getElementById(containerId);
    
    const errorHTML = `
        <div style="text-align: center; padding: 100px 20px;">
            <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
            <h3 style="color: #ef4444; margin-bottom: 15px;">Error Loading Data</h3>
            <p style="color: var(--gray); margin-bottom: 25px; max-width: 500px; margin-left: auto; margin-right: auto;">${message}</p>
            
            ${canRetry ? `
                <button onclick="location.reload()" class="btn btn-primary" style="margin-right: 10px;">
                    🔄 Retry
                </button>
            ` : ''}
            
            <button onclick="checkBackendStatus()" class="btn" style="background: #6b7280; color: white;">
                🔍 Check Backend Status
            </button>
            
            <div style="margin-top: 30px; padding: 20px; background: #f9fafb; border-radius: 8px; max-width: 600px; margin-left: auto; margin-right: auto; text-align: left;">
                <p style="font-size: 14px; font-weight: 600; margin-bottom: 10px;">🔧 Troubleshooting:</p>
                <ul style="font-size: 13px; color: #6b7280; padding-left: 20px;">
                    <li>Make sure backend is running: <code>python -m backend.api.main</code></li>
                    <li>Check backend URL: <code>${API_BASE}</code></li>
                    <li>First run can take 2-3 minutes to load AI models</li>
                    <li>Check browser console (F12) for detailed errors</li>
                </ul>
            </div>
        </div>
    `;
    
    container.innerHTML = errorHTML;
}

async function checkBackendStatus() {
    const statusDiv = document.createElement('div');
    statusDiv.style.cssText = 'position: fixed; top: 20px; right: 20px; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 9999; max-width: 400px;';
    statusDiv.innerHTML = '<p>🔍 Checking backend status...</p>';
    document.body.appendChild(statusDiv);
    
    try {
        const response = await fetch(`${API_BASE}/health`, { timeout: 5000 });
        const data = await response.json();
        
        statusDiv.innerHTML = `
            <h4 style="margin: 0 0 10px 0; color: #10b981;">✅ Backend is Running!</h4>
            <p style="margin: 5px 0; font-size: 14px;">Status: ${data.status}</p>
            <p style="margin: 5px 0; font-size: 14px;">Version: ${data.version}</p>
            <button onclick="this.parentElement.remove()" style="margin-top: 10px; padding: 5px 15px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        `;
    } catch (error) {
        statusDiv.innerHTML = `
            <h4 style="margin: 0 0 10px 0; color: #ef4444;">❌ Backend Not Reachable</h4>
            <p style="margin: 5px 0; font-size: 14px; color: #6b7280;">Error: ${error.message}</p>
            <p style="margin: 10px 0; font-size: 13px;">Make sure backend is running on ${API_BASE}</p>
            <button onclick="this.parentElement.remove()" style="margin-top: 10px; padding: 5px 15px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">
                Close
            </button>
        `;
    }
    
    setTimeout(() => {
        if (statusDiv.parentElement) {
            statusDiv.remove();
        }
    }, 10000);
}

// ============================================
// DASHBOARD LOADING
// ============================================

async function loadDashboard() {
    try {
        showLoading('content-area', 'Loading Dashboard...', 'Fetching statistics from all facilities');
        
        const data = await apiCallWithTimeout('/api/dashboard/stats');
        dashboardData = data;
        
        // Clear loading timeout
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        renderDashboard(data);
        updateLastUpdated();
        
    } catch (error) {
        console.error('Dashboard load error:', error);
        showError('content-area', error.message, true);
    }
}

function renderDashboard(data) {
    const html = `
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Facilities</h3>
                    <p>${formatNumber(data.total_facilities || 0)}</p>
                    <span>${data.operational_facilities || 0} operational</span>
                </div>
                <div class="stat-icon green">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Patients</h3>
                    <p>${formatNumber(data.total_patients || 0)}</p>
                </div>
                <div class="stat-icon blue">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Inventory Items</h3>
                    <p>${formatNumber(data.total_inventory_items || 0)}</p>
                    <span>${data.low_stock_items || 0} low stock</span>
                </div>
                <div class="stat-icon purple">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Health Workers</h3>
                    <p>${formatNumber(data.total_health_workers || 0)}</p>
                </div>
                <div class="stat-icon yellow">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                    </svg>
                </div>
            </div>
        </div>

        <!-- Alert for Low Stock -->
        ${data.low_stock_items > 0 ? `
        <div class="alert alert-warning mb-3">
            <strong>⚠️ Attention:</strong> ${data.low_stock_items} items are running low on stock and need immediate attention.
        </div>
        ` : ''}

        <!-- Charts Grid -->
        <div class="grid-2">
            <div class="chart-card">
                <h3>Patient Demographics</h3>
                <div class="stats-grid">
                    <div style="text-align: center; padding: 20px; background: #dbeafe; border-radius: 8px;">
                        <p style="font-size: 14px; color: #1e40af; margin-bottom: 8px;">Male</p>
                        <p style="font-size: 24px; font-weight: 700; color: #1e40af;">
                            ${formatNumber(data.recent_patient_stats?.male_count || 0)}
                        </p>
                    </div>
                    <div style="text-align: center; padding: 20px; background: #fce7f3; border-radius: 8px;">
                        <p style="font-size: 14px; color: #be123c; margin-bottom: 8px;">Female</p>
                        <p style="font-size: 24px; font-weight: 700; color: #be123c;">
                            ${formatNumber(data.recent_patient_stats?.female_count || 0)}
                        </p>
                    </div>
                </div>
            </div>

            <div class="chart-card">
                <h3>Disease Statistics</h3>
                <div class="stats-grid">
                    <div style="text-align: center; padding: 20px; background: #dbeafe; border-radius: 8px;">
                        <p style="font-size: 14px; color: #1e40af; margin-bottom: 8px;">Total Cases</p>
                        <p style="font-size: 24px; font-weight: 700; color: #1e40af;">
                            ${formatNumber(data.disease_stats?.total_cases || 0)}
                        </p>
                    </div>
                    <div style="text-align: center; padding: 20px; background: #fee2e2; border-radius: 8px;">
                        <p style="font-size: 14px; color: #991b1b; margin-bottom: 8px;">Case Fatality Rate</p>
                        <p style="font-size: 24px; font-weight: 700; color: #991b1b;">
                            ${data.disease_stats?.case_fatality_rate || 0}%
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Top Diagnoses -->
        ${data.recent_patient_stats?.top_diagnoses?.length > 0 ? `
        <div class="chart-card">
            <h3>Top Diagnoses</h3>
            <div style="padding: 20px;">
                ${data.recent_patient_stats.top_diagnoses.slice(0, 5).map(d => `
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-weight: 500;">${d.diagnosis}</span>
                            <span style="color: var(--gray);">${formatNumber(d.count)} cases</span>
                        </div>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: var(--primary); height: 100%; width: ${(d.count / data.recent_patient_stats.top_diagnoses[0].count) * 100}%;"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('content-area').innerHTML = html;
}

// ============================================
// FACILITIES
// ============================================

async function loadFacilities() {
    try {
        showLoading('content-area', 'Loading Facilities...', 'Fetching facility information');
        
        const data = await apiCallWithTimeout('/api/dashboard/facilities?operational_only=false');
        
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        renderFacilities(data.facilities || []);
        
    } catch (error) {
        console.error('Facilities load error:', error);
        showError('content-area', error.message, true);
    }
}

function renderFacilities(facilities) {
    const html = `
        <div class="table-card">
            <h3>Healthcare Facilities (${facilities.length})</h3>
            ${facilities.length > 0 ? `
            <table>
                <thead>
                    <tr>
                        <th>Facility Name</th>
                        <th>State</th>
                        <th>LGA</th>
                        <th>Status</th>
                        <th>Workers</th>
                    </tr>
                </thead>
                <tbody>
                    ${facilities.slice(0, 50).map(f => `
                        <tr>
                            <td>${f.facility_name || 'N/A'}</td>
                            <td>${f.state || 'N/A'}</td>
                            <td>${f.lga || 'N/A'}</td>
                            <td>
                                <span class="status-badge ${f.operational_status?.includes('Functional') ? 'status-operational' : 'status-non-operational'}">
                                    ${f.operational_status || 'Unknown'}
                                </span>
                            </td>
                            <td>${f.health_workers || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
            ${facilities.length > 50 ? `<p style="padding: 10px; text-align: center; color: var(--gray); font-size: 14px;">Showing first 50 of ${facilities.length} facilities</p>` : ''}
            ` : '<p style="padding: 40px; text-align: center; color: var(--gray);">No facilities data available</p>'}
        </div>
    `;
    
    document.getElementById('content-area').innerHTML = html;
}

// ============================================
// PATIENTS
// ============================================

async function loadPatients() {
    try {
        showLoading('content-area', 'Loading Patient Data...', 'Analyzing patient statistics');
        
        const data = await apiCallWithTimeout('/api/dashboard/patients/stats?days=30');
        
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        renderPatients(data.statistics);
        
    } catch (error) {
        console.error('Patients load error:', error);
        showError('content-area', error.message, true);
    }
}

function renderPatients(stats) {
    const html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Patients</h3>
                    <p>${formatNumber(stats.total_patients || 0)}</p>
                </div>
                <div class="stat-icon blue">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                        <circle cx="9" cy="7" r="4"></circle>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Male Patients</h3>
                    <p>${formatNumber(stats.male_count || 0)}</p>
                    <span>${stats.total_patients > 0 ? ((stats.male_count / stats.total_patients) * 100).toFixed(1) : '0'}%</span>
                </div>
                <div class="stat-icon blue">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Female Patients</h3>
                    <p>${formatNumber(stats.female_count || 0)}</p>
                    <span>${stats.total_patients > 0 ? ((stats.female_count / stats.total_patients) * 100).toFixed(1) : '0'}%</span>
                </div>
                <div class="stat-icon pink">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Average Age</h3>
                    <p>${stats.average_age || 0} <span style="font-size: 16px;">years</span></p>
                </div>
                <div class="stat-icon purple">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"></circle>
                    </svg>
                </div>
            </div>
        </div>

        ${stats.top_diagnoses && stats.top_diagnoses.length > 0 ? `
        <div class="chart-card mt-3">
            <h3>Top Diagnoses (Last 30 Days)</h3>
            <div style="padding: 20px;">
                ${stats.top_diagnoses.slice(0, 10).map(d => `
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                            <span style="font-weight: 500;">${d.diagnosis}</span>
                            <span style="color: var(--gray);">${formatNumber(d.count)} cases</span>
                        </div>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; overflow: hidden;">
                            <div style="background: var(--primary); height: 100%; width: ${(d.count / stats.top_diagnoses[0].count) * 100}%;"></div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
        ` : '<div class="chart-card mt-3"><p style="padding: 40px; text-align: center; color: var(--gray);">No diagnosis data available</p></div>'}
    `;
    
    document.getElementById('content-area').innerHTML = html;
}

// ============================================
// INVENTORY
// ============================================

async function loadInventory() {
    try {
        showLoading('content-area', 'Loading Inventory...', 'Analyzing stock levels');
        
        const dashData = await apiCallWithTimeout('/api/dashboard/stats');
        
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        renderInventory(dashData);
        
    } catch (error) {
        console.error('Inventory load error:', error);
        showError('content-area', error.message, true);
    }
}

function renderInventory(data) {
    const html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Items</h3>
                    <p>${formatNumber(data.total_inventory_items || 0)}</p>
                </div>
                <div class="stat-icon blue">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Low Stock Items</h3>
                    <p>${formatNumber(data.low_stock_items || 0)}</p>
                </div>
                <div class="stat-icon yellow">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Stock Health</h3>
                    <p>${data.total_inventory_items > 0 ? (((data.total_inventory_items - data.low_stock_items) / data.total_inventory_items) * 100).toFixed(1) : 0}%</p>
                </div>
                <div class="stat-icon green">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                </div>
            </div>
        </div>

        ${data.low_stock_items > 0 ? `
        <div class="alert alert-warning mt-3">
            <strong>⚠️ Low Stock Alert:</strong> ${data.low_stock_items} items are running low on stock and need immediate attention.
        </div>
        ` : ''}

        <div class="chart-card mt-3">
            <h3>Inventory Overview</h3>
            <div style="text-align: center; padding: 40px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto 20px; display: block; color: var(--primary);">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                </svg>
                <p style="font-size: 18px; color: var(--gray);">
                    Monitoring ${formatNumber(data.total_inventory_items || 0)} items across all facilities
                </p>
            </div>
        </div>
    `;
    
    document.getElementById('content-area').innerHTML = html;
}

// ============================================
// DISEASES
// ============================================

async function loadDiseases() {
    try {
        showLoading('content-area', 'Loading Disease Data...', 'Analyzing disease statistics');
        
        const dashData = await apiCallWithTimeout('/api/dashboard/stats');
        
        if (loadingTimeout) {
            clearTimeout(loadingTimeout);
        }
        
        renderDiseases(dashData.disease_stats || {});
        
    } catch (error) {
        console.error('Diseases load error:', error);
        showError('content-area', error.message, true);
    }
}

function renderDiseases(diseaseStats) {
    const html = `
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Cases</h3>
                    <p>${formatNumber(diseaseStats.total_cases || 0)}</p>
                </div>
                <div class="stat-icon blue">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Total Deaths</h3>
                    <p>${formatNumber(diseaseStats.total_deaths || 0)}</p>
                </div>
                <div class="stat-icon red">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="15" y1="9" x2="9" y2="15"></line>
                        <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-info">
                    <h3>Case Fatality Rate</h3>
                    <p>${diseaseStats.case_fatality_rate || 0}%</p>
                </div>
                <div class="stat-icon yellow">
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                    </svg>
                </div>
            </div>
        </div>

        <div class="chart-card mt-3">
            <h3>Disease Surveillance</h3>
            <div style="text-align: center; padding: 40px;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" style="margin: 0 auto 20px; display: block; color: var(--danger);">
                    <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline>
                </svg>
                <p style="font-size: 18px; color: var(--gray); margin-bottom: 10px;">
                    Monitoring disease trends across all facilities
                </p>
                <p style="font-size: 14px; color: var(--gray);">
                    Total cases tracked: ${formatNumber(diseaseStats.total_cases || 0)}
                </p>
            </div>
        </div>
    `;
    
    document.getElementById('content-area').innerHTML = html;
}

// ============================================
// AI TRIAGE
// ============================================

function loadTriage() {
    // Load triage page from chat.js
    if (typeof loadTriagePage === 'function') {
        loadTriagePage();
    } else {
        showError('content-area', 'AI Triage module not loaded. Make sure chat.js is included.', false);
    }
}

// ============================================
// UTILITIES
// ============================================

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

function updateLastUpdated() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    const updateEl = document.getElementById('last-updated');
    if (updateEl) {
        updateEl.textContent = `Last updated: ${timeString}`;
    }
}

// ============================================
// NAVIGATION
// ============================================

function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Get page from data attribute
            const page = this.dataset.page;
            
            // Update page title
            const pageTitle = document.getElementById('page-title');
            if (pageTitle) {
                pageTitle.textContent = this.querySelector('span').textContent;
            }
            
            // Load corresponding page
            switch(page) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'facilities':
                    loadFacilities();
                    break;
                case 'patients':
                    loadPatients();
                    break;
                case 'inventory':
                    loadInventory();
                    break;
                case 'diseases':
                    loadDiseases();
                    break;
                case 'triage':
                    loadTriage();
                    break;
                default:
                    console.error('Unknown page:', page);
            }
        });
    });
}

// ============================================
// INITIALIZATION
// ============================================

if (window.location.pathname.includes('dashboard.html')) {
    // Check authentication
    if (typeof checkAuth === 'function') {
        checkAuth();
    }
    
    // Setup navigation
    setupNavigation();
    
    // Load dashboard (with improved error handling)
    console.log('🚀 Initializing dashboard...');
    loadDashboard();
}

console.log('✅ Dashboard.js loaded with improved timeout handling');