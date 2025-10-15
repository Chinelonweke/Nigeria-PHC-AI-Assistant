/**
 * Inventory Management UI
 * Handles stockout predictions and alerts
 */

const API_BASE = 'http://localhost:8000/api/inventory';

// Load inventory data on page load
document.addEventListener('DOMContentLoaded', () => {
    loadInventoryData();
    
    // Auto-refresh every 5 minutes
    setInterval(loadInventoryData, 300000);
});

async function loadInventoryData() {
    try {
        // Load status
        const statusRes = await fetch(`${API_BASE}/status`);
        const status = await statusRes.json();
        
        updateSummary(status);
        
        // Load predictions
        const predsRes = await fetch(`${API_BASE}/predict-stockouts`);
        const predictions = await predsRes.json();
        
        displayPredictions(predictions);
        
    } catch (error) {
        console.error('Error loading inventory:', error);
        showError('Failed to load inventory data');
    }
}

function updateSummary(status) {
    document.getElementById('totalItems').textContent = status.total_items || 0;
    document.getElementById('criticalCount').textContent = status.critical_count || 0;
    document.getElementById('warningCount').textContent = status.low_stock_count || 0;
}

function displayPredictions(data) {
    const container = document.getElementById('predictions-list');
    const predictions = data.predictions || [];
    
    if (predictions.length === 0) {
        container.innerHTML = '<p style="color: #10b981">✅ All items adequately stocked!</p>';
        return;
    }
    
    // Filter only alerts (not OK items)
    const alerts = predictions.filter(p => 
        ['CRITICAL', 'WARNING', 'ATTENTION'].includes(p.alert_level)
    );
    
    if (alerts.length === 0) {
        container.innerHTML = '<p style="color: #10b981">✅ No alerts - all items adequately stocked!</p>';
        return;
    }
    
    container.innerHTML = alerts.map(pred => `
        <div class="alert-card alert-${pred.alert_level}">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div>
                    <h4 style="margin: 0 0 8px 0;">${pred.item_name}</h4>
                    <p style="margin: 4px 0; font-size: 14px; color: #6b7280;">
                        📍 ${pred.facility_id}
                    </p>
                    <p style="margin: 4px 0;">
                        <span class="stock-badge badge-${pred.alert_level.toLowerCase()}">
                            ${pred.alert_level}
                        </span>
                    </p>
                </div>
                
                <div style="text-align: right;">
                    <p style="margin: 0; font-size: 24px; font-weight: 600;">
                        ${pred.current_stock}
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #6b7280;">
                        units left
                    </p>
                </div>
            </div>
            
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(0,0,0,0.1);">
                <p style="margin: 4px 0; font-size: 14px;">
                    ⏰ <strong>Days until reorder:</strong> ${Math.round(pred.days_until_reorder)} days
                </p>
                <p style="margin: 4px 0; font-size: 14px;">
                    📊 <strong>Daily usage:</strong> ~${pred.daily_usage_estimate} units/day
                </p>
                <p style="margin: 4px 0; font-size: 14px;">
                    📦 <strong>Recommended order:</strong> ${pred.recommended_order_quantity} units
                </p>
            </div>
            
            <div style="margin-top: 12px; padding: 10px; background: rgba(255,255,255,0.5); border-radius: 4px;">
                <p style="margin: 0; font-size: 13px; font-style: italic;">
                    ${pred.message}
                </p>
            </div>
        </div>
    `).join('');
}

function showError(message) {
    const container = document.getElementById('predictions-list');
    container.innerHTML = `
        <div style="padding: 20px; text-align: center; color: #e53e3e;">
            <p>❌ ${message}</p>
            <button onclick="loadInventoryData()" class="btn btn-primary">Try Again</button>
        </div>
    `;
}

function refreshData() {
    loadInventoryData();
}